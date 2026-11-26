//! Arranque del server compartido desde la ventana (spec 005, D-2; spec 028): `studio api up --with-token` y su línea `ready`.

use std::ffi::OsString;
use std::path::Path;
use std::process::{Command, Stdio};

/// Por qué no hubo server. El código llega a la pantalla de error, que lo traduce con el catálogo.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ServerError {
    Spawn,
    Timeout,
    Exited,
    /// Un paso de la preparación de la app instalada (spec 022), con su código.
    Bootstrap(&'static str),
}

impl ServerError {
    pub fn code(self) -> &'static str {
        match self {
            ServerError::Spawn => "server_spawn_failed",
            ServerError::Timeout => "server_timeout",
            ServerError::Exited => "server_exited",
            ServerError::Bootstrap(code) => code,
        }
    }
}

/// Lo que dice `studio` al terminar: si salió con 0 y lo que imprimió.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Run {
    pub success: bool,
    pub stdout: String,
}

/// La dirección del server compartido, con su token y su versión (spec 028, `api.json`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Ready {
    pub url: String,
    pub token: String,
    pub version: String,
}

/// La línea `{"ready": {...}}` de `studio api up --with-token`. Cualquier otra salida no es una dirección.
pub fn parse_ready(text: &str) -> Option<Ready> {
    let value: serde_json::Value = serde_json::from_str(text.trim()).ok()?;
    let ready = value.get("ready")?;
    Some(Ready {
        url: ready.get("url")?.as_str()?.to_string(),
        token: ready.get("token")?.as_str()?.to_string(),
        version: ready.get("version")?.as_str()?.to_string(),
    })
}

/// `<programa> <antes…> <args…>` esperando a que termine, sin consola en Windows. El server que arranca `api up`
/// no hereda este pipe (su salida va a su log), así que esta espera solo dura lo que tarda `studio`.
/// shortcut: stderr va a null; el motivo de un fallo es el código de ServerError y el log del server está en logs/.
pub fn run_studio(
    program: &Path,
    before: &[OsString],
    env: &[(&str, OsString)],
    args: &[&str],
) -> Result<Run, ServerError> {
    let mut command = Command::new(program);
    command
        .envs(env.iter().map(|(key, value)| (*key, value)))
        .args(before)
        .args(args)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::null());
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(CREATE_NO_WINDOW);
    }
    let output = command.output().map_err(|_| ServerError::Spawn)?;
    Ok(Run {
        success: output.status.success(),
        stdout: String::from_utf8_lossy(&output.stdout).into_owned(),
    })
}

#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x0800_0000;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_ready_reads_the_address_token_and_version() {
        let ready = parse_ready(
            r#"{"ready": {"url": "http://127.0.0.1:41830", "port": 41830, "pid": 7, "version": "0.1.0", "token": "t"}}"#,
        )
        .expect("una línea ready válida");
        assert_eq!(ready.url, "http://127.0.0.1:41830");
        assert_eq!(ready.token, "t");
        assert_eq!(ready.version, "0.1.0");
    }

    #[test]
    fn parse_ready_ignores_other_output() {
        assert_eq!(parse_ready("INFO: uvicorn running"), None);
        assert_eq!(parse_ready(r#"{"other": 1}"#), None);
    }

    #[test]
    fn errors_have_a_stable_code_for_the_screen() {
        assert_eq!(ServerError::Spawn.code(), "server_spawn_failed");
        assert_eq!(ServerError::Timeout.code(), "server_timeout");
        assert_eq!(ServerError::Exited.code(), "server_exited");
    }
}
