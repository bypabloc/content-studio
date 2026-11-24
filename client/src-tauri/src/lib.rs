//! Content Studio (spec 005, D-2): la ventana de Tauri, el server local y el comando `get_connection`.

mod bootstrap;
mod server;

use std::io::BufReader;
use std::path::PathBuf;
use std::process::Child;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use serde::Serialize;
use tauri::webview::{PermissionKind, PermissionResponse};
use tauri::{AppHandle, Manager, RunEvent};

use server::ServerError;

const READY_TIMEOUT: Duration = Duration::from_secs(30);

#[derive(Serialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct Connection {
    base_url: String,
    token: String,
}

struct Running {
    child: Child,
    connection: Connection,
    #[cfg(windows)]
    _job: server::job::KillOnClose,
}

/// El server de la sesión: uno solo, que se reutiliza mientras siga vivo, y el modo de la app (spec 022).
#[derive(Clone)]
pub struct ServerState(Arc<Mutex<Option<Running>>>, Arc<bootstrap::Mode>);

impl ServerState {
    fn connect(&self) -> Result<Connection, ServerError> {
        let mut slot = self
            .0
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner());
        if let Some(running) = slot.as_mut() {
            if running.child.try_wait().ok().flatten().is_none() {
                return Ok(running.connection.clone());
            }
        }
        *slot = None;

        let token = new_token();
        let mut child = server::spawn(&project_root(), &token, &self.1.server_env())?;
        // En Windows el proceso nace suspendido: el Job lo recibe y solo después corre, así sus hijos quedan en el Job.
        #[cfg(windows)]
        let job = match server::job::KillOnClose::assign(&child)
            .and_then(|job| server::job::resume(&child).map(|()| job))
        {
            Ok(job) => job,
            Err(_) => {
                let _ = child.kill();
                return Err(ServerError::Spawn);
            }
        };
        let stdout = child.stdout.take().ok_or(ServerError::Spawn)?;
        let port = match server::wait_for_ready(BufReader::new(stdout), READY_TIMEOUT) {
            Ok(port) => port,
            Err(error) => {
                let _ = child.kill();
                let _ = child.wait();
                return Err(error);
            }
        };
        let connection = Connection {
            base_url: format!("http://127.0.0.1:{port}"),
            token,
        };
        *slot = Some(Running {
            child,
            connection: connection.clone(),
            #[cfg(windows)]
            _job: job,
        });
        Ok(connection)
    }

    fn stop(&self) {
        let mut slot = self
            .0
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner());
        if let Some(mut running) = slot.take() {
            let _ = running.child.kill();
            let _ = running.child.wait();
        }
    }
}

fn new_token() -> String {
    let mut bytes = [0u8; 32];
    getrandom::fill(&mut bytes).expect("el sistema debe dar bytes aleatorios");
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

/// En desarrollo, la raíz del checkout (`client/src-tauri/../..`); la 015 la cambia por el uv incluido.
fn project_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
}

/// Async: la espera del `ready` bloquea hasta 30 s, así que va en un hilo aparte y no congela la ventana.
#[tauri::command]
async fn get_connection(app: AppHandle) -> Result<Connection, String> {
    let state = app.state::<ServerState>().inner().clone();
    tauri::async_runtime::spawn_blocking(move || state.connect())
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
        .setup(|app| {
            let resources = app.path().resource_dir().unwrap_or_default();
            let mode = bootstrap::current_mode(resources);
            app.manage(ServerState(Arc::default(), Arc::new(mode)));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_connection])
        .build(tauri::generate_context!())
        .expect("Content Studio no pudo arrancar")
        .run(|app, event| {
            if let RunEvent::Exit = event {
                app.state::<ServerState>().stop();
            }
        });
}
