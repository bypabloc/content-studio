//! Content Studio (spec 005, D-2; spec 028): la ventana de Tauri, el server compartido y el comando `get_connection`.

mod bootstrap;
mod server;

use std::ffi::OsString;
use std::path::PathBuf;
use std::sync::Arc;

use serde::Serialize;
use tauri::webview::{PermissionKind, PermissionResponse};
use tauri::{AppHandle, Emitter, Manager};

use server::{Ready, Run, ServerError};

#[derive(Serialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct Connection {
    base_url: String,
    token: String,
}

/// El server compartido de la instalación. La ventana se adjunta: no lo posee, así que sobrevive a su cierre (D-6).
#[derive(Clone)]
pub struct ServerState(Arc<bootstrap::Mode>, String);

/// `studio api up --with-token`: arranca el server si no está vivo, o reutiliza el que responde (AC-1, AC-2).
fn up(run: &mut dyn FnMut(&[&str]) -> Result<Run, ServerError>) -> Result<Ready, ServerError> {
    let answer = run(&["api", "up", "--with-token"])?;
    if !answer.success {
        return Err(ServerError::Exited);
    }
    server::parse_ready(&answer.stdout).ok_or(ServerError::Exited)
}

/// Se adjunta al server compartido. Si es de otra versión, pide `api down` (sin fuerza: con un trabajo activo se niega
/// y la ventana se queda con el server viejo) y arranca el de esta versión (AC-7, AC-9).
pub fn attach(
    run: &mut dyn FnMut(&[&str]) -> Result<Run, ServerError>,
    app_version: &str,
) -> Result<Connection, ServerError> {
    let mut ready = up(run)?;
    if ready.version != app_version {
        run(&["api", "down"])?;
        ready = up(run)?;
    }
    Ok(Connection {
        base_url: ready.url,
        token: ready.token,
    })
}

/// Detiene el server compartido antes de instalar una actualización: `api down --force`, también con trabajos
/// corriendo (AC-9). Si `studio` se niega, la instalación no sigue: reemplazar archivos bajo un server vivo no.
pub fn stop(run: &mut dyn FnMut(&[&str]) -> Result<Run, ServerError>) -> Result<(), ServerError> {
    let answer = run(&["api", "down", "--force"])?;
    if answer.success {
        Ok(())
    } else {
        Err(ServerError::Exited)
    }
}

impl ServerState {
    /// Qué ejecutar para hablar con `studio`: `uv run --project <raíz> studio` en un checkout, el de su venv instalado.
    fn launcher(&self) -> (PathBuf, Vec<OsString>) {
        match self.0.as_ref() {
            bootstrap::Mode::Dev { .. } => {
                let before: Vec<OsString> = vec![
                    "run".into(),
                    "--project".into(),
                    project_root().into_os_string(),
                    "studio".into(),
                ];
                (PathBuf::from("uv"), before)
            }
            bootstrap::Mode::Installed { resources } => {
                let layout = bootstrap::Layout::from_env(resources.clone(), &self.1);
                (layout.studio(), Vec::new())
            }
        }
    }

    /// Prepara la app instalada (Python, venv y datos; `emit` avisa cada paso) y se adjunta al server.
    fn connect(&self, mut emit: impl FnMut(bootstrap::Progress)) -> Result<Connection, ServerError> {
        if let bootstrap::Mode::Installed { resources } = self.0.as_ref() {
            let layout = bootstrap::Layout::from_env(resources.clone(), &self.1);
            let mut runner = bootstrap::CommandRunner { log: layout.log() };
            bootstrap::prepare(&layout, &mut runner, &mut emit).map_err(ServerError::Bootstrap)?;
        }
        let (program, before) = self.launcher();
        let env = self.0.server_env();
        attach(&mut |args| server::run_studio(&program, &before, &env, args), &self.1)
    }

    /// Antes de instalar una actualización, detiene el server aunque tenga trabajos (spec 028, AC-9).
    fn stop_for_update(&self) -> Result<(), ServerError> {
        let (program, before) = self.launcher();
        let env = self.0.server_env();
        stop(&mut |args| server::run_studio(&program, &before, &env, args))
    }
}

/// En desarrollo, la raíz del checkout (`client/src-tauri/../..`); la 015 la cambia por el uv incluido.
fn project_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..").join("..")
}

/// Async: el arranque del server bloquea hasta que responde, así que va en un hilo aparte y no congela la ventana.
#[tauri::command]
async fn get_connection(app: AppHandle) -> Result<Connection, String> {
    let state = app.state::<ServerState>().inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        state.connect(|progress| {
            let _ = app.emit("bootstrap", progress);
        })
    })
    .await
    .map_err(|error| error.to_string())?
    .map_err(|error| error.code().to_string())
}

/// Lo llama el client antes de instalar una actualización (spec 028, AC-9).
#[tauri::command]
async fn stop_server_for_update(app: AppHandle) -> Result<(), String> {
    let state = app.state::<ServerState>().inner().clone();
    tauri::async_runtime::spawn_blocking(move || state.stop_for_update())
        .await
        .map_err(|error| error.to_string())?
        .map_err(|error| error.code().to_string())
}

pub fn run() {
    tauri::Builder::default()
        // La app graba con su propio micrófono: WebView2 lo concede sin preguntar. Que se está usando lo muestra el
        // indicador «Micrófono en uso» de la grabación (spec 010, D-2). Lo demás sigue la decisión por defecto.
        .on_permission_request(|_, kind| match kind {
            PermissionKind::Microphone => PermissionResponse::Allow,
            _ => PermissionResponse::Default,
        })
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_window_state::Builder::default().build())
        .plugin(tauri_plugin_process::init())
        .setup(|app| {
            let resources = app.path().resource_dir().unwrap_or_default();
            let mode = bootstrap::current_mode(resources);
            // Solo la app instalada se actualiza (spec 022, D-6): en un checkout, `check()` del client falla y no ofrece nada.
            if matches!(mode, bootstrap::Mode::Installed { .. }) {
                app.handle()
                    .plugin(tauri_plugin_updater::Builder::new().build())?;
            }
            let version = app.package_info().version.to_string();
            app.manage(ServerState(Arc::new(mode), version));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_connection, stop_server_for_update])
        .build(tauri::generate_context!())
        .expect("Content Studio no pudo arrancar")
        .run(|_, _| {});
}

#[cfg(test)]
mod tests {
    use super::*;

    const READY_0_1_0: &str = r#"{"ready": {"url": "http://127.0.0.1:41830", "port": 41830, "pid": 7, "version": "0.1.0", "token": "t1"}}"#;
    const READY_0_2_0: &str = r#"{"ready": {"url": "http://127.0.0.1:41830", "port": 41830, "pid": 9, "version": "0.2.0", "token": "t2"}}"#;

    fn answer(stdout: &str) -> server::Run {
        server::Run {
            success: true,
            stdout: stdout.to_string(),
        }
    }

    #[test]
    fn connect_attaches_to_running_server() {
        let mut calls: Vec<String> = Vec::new();
        let connection = attach(
            &mut |args| {
                calls.push(args.join(" "));
                Ok(answer(READY_0_1_0))
            },
            "0.1.0",
        )
        .expect("la ventana se adjunta al server que responde");
        assert_eq!(connection.base_url, "http://127.0.0.1:41830");
        assert_eq!(connection.token, "t1");
        assert_eq!(calls, vec!["api up --with-token"]);
    }

    #[test]
    fn restarts_server_of_other_version() {
        let mut calls: Vec<String> = Vec::new();
        let mut answers = vec![answer(READY_0_1_0), answer(""), answer(READY_0_2_0)].into_iter();
        let connection = attach(
            &mut |args| {
                calls.push(args.join(" "));
                Ok(answers.next().expect("una respuesta por llamada"))
            },
            "0.2.0",
        )
        .expect("el server de otra versión se reemplaza");
        assert_eq!(
            calls,
            vec!["api up --with-token", "api down", "api up --with-token"]
        );
        assert_eq!(connection.token, "t2");
    }

    #[test]
    fn stop_asks_for_force() {
        let mut calls: Vec<String> = Vec::new();
        stop(&mut |args| {
            calls.push(args.join(" "));
            Ok(answer(""))
        })
        .expect("el server se detiene");
        assert_eq!(calls, vec!["api down --force"]);
    }

    #[test]
    fn stop_fails_when_studio_refuses() {
        let result = stop(&mut |_| {
            Ok(server::Run {
                success: false,
                stdout: String::new(),
            })
        });
        assert_eq!(result.err(), Some(ServerError::Exited));
    }

    #[test]
    fn a_failing_up_is_reported_as_exited() {
        let result = attach(
            &mut |_| {
                Ok(server::Run {
                    success: false,
                    stdout: String::new(),
                })
            },
            "0.1.0",
        );
        assert_eq!(result.err(), Some(ServerError::Exited));
    }
}
