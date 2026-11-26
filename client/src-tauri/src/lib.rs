//! Content Studio (spec 005, D-2; spec 028): la ventana de Tauri, el server compartido y el comando `get_connection`.

mod bootstrap;
mod external;
mod firewall;
mod server;
mod startup;

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

/// Cambia el token (spec 028): `api down` primero, que se niega con trabajos activos y entonces el token no cambia;
/// con el server parado, `api token --rotate` escribe el nuevo. La ventana se reconecta después con `get_connection`.
pub fn rotate(run: &mut dyn FnMut(&[&str]) -> Result<Run, ServerError>) -> Result<(), ServerError> {
    if !run(&["api", "down"])?.success {
        return Err(ServerError::Exited);
    }
    if run(&["api", "token", "--rotate"])?.success {
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

    /// Cambia el token con el server parado (spec 028, AC-11).
    fn change_token(&self) -> Result<(), ServerError> {
        let (program, before) = self.launcher();
        let env = self.0.server_env();
        rotate(&mut |args| server::run_studio(&program, &before, &env, args))
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
/// «Iniciar el servidor con Windows» (spec 031, AC-8): activa o quita el valor `Run` de HKCU. Quitarlo no necesita venv.
#[tauri::command]
fn set_start_at_login(enabled: bool, state: tauri::State<'_, ServerState>) -> Result<(), String> {
    if !enabled {
        return startup::apply(&mut startup::CurrentUserRun, false, "");
    }
    let venv = bootstrap::installed_venv(&state.0, &state.1).ok_or("solo en la app instalada")?;
    startup::apply(&mut startup::CurrentUserRun, true, &startup::server_command(&venv))
}

/// Red local (spec 032, AC-9): crea o borra la regla «Content Studio LAN» del perfil Privado; pide elevación (UAC).
#[tauri::command]
async fn set_lan_firewall(enabled: bool, port: u16) -> Result<(), String> {
    tauri::async_runtime::spawn_blocking(move || firewall::apply(&mut firewall::RunAs, enabled, port))
        .await
        .map_err(|error| error.to_string())?
}

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

/// Lo llama el panel de Integraciones (spec 028, AC-11): cambia el token y el client se reconecta con `get_connection`.
#[tauri::command]
async fn rotate_token(app: AppHandle) -> Result<(), String> {
    let state = app.state::<ServerState>().inner().clone();
    tauri::async_runtime::spawn_blocking(move || state.change_token())
        .await
        .map_err(|error| error.to_string())?
        .map_err(|error| error.code().to_string())
}

pub fn run() {
    tauri::Builder::default()
        // Instancia única primero (AC-5): un segundo arranque por enlace o «Enviar a» le pasa su argv a esta ventana.
        .plugin(tauri_plugin_single_instance::init(|app, argv, _cwd| {
            external::forward_argv(&argv, |payload| {
                let _ = app.emit(external::EVENT, payload);
            });
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.unminimize();
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_deep_link::init())
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
        .invoke_handler(tauri::generate_handler![get_connection, stop_server_for_update, rotate_token, external::startup_argv, external::path_exists, set_start_at_login, set_lan_firewall])
        .build(tauri::generate_context!())
        .expect("Content Studio no pudo arrancar")
        .run(|_, _| {});
}

#[cfg(test)]
mod tests;
