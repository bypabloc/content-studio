//! Arranque del server local (spec 005, D-2): `studio serve --port 0 --token <t>` y la línea `ready` con el puerto.

use std::io::BufRead;
use std::path::Path;
use std::process::{Child, Command, Stdio};
use std::sync::mpsc::{self, RecvTimeoutError};
use std::thread;
use std::time::Duration;

/// Por qué no hubo server. El código llega a la pantalla de error, que lo traduce con el catálogo.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ServerError {
    Spawn,
    Timeout,
    Exited,
}

impl ServerError {
    pub fn code(self) -> &'static str {
        match self {
            ServerError::Spawn => "server_spawn_failed",
            ServerError::Timeout => "server_timeout",
            ServerError::Exited => "server_exited",
        }
    }
}

/// La línea `ready` de `studio serve`: `{"ready": {"port": n}}`. Cualquier otra línea no es el puerto.
pub fn parse_ready(line: &str) -> Option<u16> {
    let value: serde_json::Value = serde_json::from_str(line.trim()).ok()?;
    u16::try_from(value.get("ready")?.get("port")?.as_u64()?).ok()
}

/// Lee la salida hasta la línea `ready`. Sigue drenando la salida después, para que el server no se bloquee.
pub fn wait_for_ready(
    lines: impl BufRead + Send + 'static,
    timeout: Duration,
) -> Result<u16, ServerError> {
    let (sender, receiver) = mpsc::channel();
    thread::spawn(move || {
        let mut sent = false;
        for line in lines.lines().map_while(Result::ok) {
            if !sent {
                if let Some(port) = parse_ready(&line) {
                    sent = true;
                    let _ = sender.send(Some(port));
                }
            }
        }
        if !sent {
            let _ = sender.send(None);
        }
    });
    match receiver.recv_timeout(timeout) {
        Ok(Some(port)) => Ok(port),
        Ok(None) | Err(RecvTimeoutError::Disconnected) => Err(ServerError::Exited),
        Err(RecvTimeoutError::Timeout) => Err(ServerError::Timeout),
    }
}

/// `uv run --project <raíz> studio serve --port 0 --token <t>`, sin consola en Windows.
/// shortcut: stderr va a null, así que el motivo de un fallo es el código de ServerError y no el log; subir cuando haya pantalla de log.
pub fn spawn(project: &Path, token: &str) -> Result<Child, ServerError> {
    let mut command = Command::new("uv");
    command
        .args(["run", "--project"])
        .arg(project)
        .args(["studio", "serve", "--port", "0", "--token", token])
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::null());
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(CREATE_NO_WINDOW);
    }
    command.spawn().map_err(|_| ServerError::Spawn)
}

#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x0800_0000;

/// Un Job Object con KILL_ON_JOB_CLOSE: el server muere con la ventana aunque la app se cierre mal (D-2).
#[cfg(windows)]
pub mod job {
    use std::os::windows::io::AsRawHandle;
    use std::process::Child;

    use windows::Win32::Foundation::{CloseHandle, HANDLE};
    use windows::Win32::System::JobObjects::{
        AssignProcessToJobObject, CreateJobObjectW, JobObjectExtendedLimitInformation,
        SetInformationJobObject, JOBOBJECT_EXTENDED_LIMIT_INFORMATION,
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    };

    pub struct KillOnClose(HANDLE);

    // El HANDLE solo se usa para cerrarlo en Drop; el Job no se comparte entre hilos.
    unsafe impl Send for KillOnClose {}
    unsafe impl Sync for KillOnClose {}

    impl KillOnClose {
        pub fn assign(child: &Child) -> windows::core::Result<Self> {
            let mut info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION::default();
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
            unsafe {
                let job = CreateJobObjectW(None, None)?;
                let size = std::mem::size_of::<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>() as u32;
                SetInformationJobObject(
                    job,
                    JobObjectExtendedLimitInformation,
                    &info as *const _ as *const _,
                    size,
                )?;
                AssignProcessToJobObject(job, HANDLE(child.as_raw_handle()))?;
                Ok(Self(job))
            }
        }
    }

    impl Drop for KillOnClose {
        fn drop(&mut self) {
            unsafe {
                let _ = CloseHandle(self.0);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{BufReader, Read};

    #[test]
    fn parse_ready_reads_the_port_of_the_ready_line() {
        assert_eq!(parse_ready(r#"{"ready": {"port": 8123}}"#), Some(8123));
    }

    #[test]
    fn parse_ready_ignores_other_lines() {
        assert_eq!(parse_ready("INFO: uvicorn running"), None);
        assert_eq!(parse_ready(r#"{"other": 1}"#), None);
    }

    #[test]
    fn wait_for_ready_skips_noise_until_the_ready_line() {
        let lines =
            std::io::Cursor::new("cargando modelo\n{\"ready\": {\"port\": 9001}}\n".to_string());
        assert_eq!(wait_for_ready(lines, Duration::from_secs(5)), Ok(9001));
    }

    #[test]
    fn wait_for_ready_fails_when_the_process_exits_first() {
        let lines = std::io::Cursor::new("error al arrancar\n".to_string());
        assert_eq!(
            wait_for_ready(lines, Duration::from_secs(5)),
            Err(ServerError::Exited)
        );
    }

    struct Stalled;

    impl Read for Stalled {
        fn read(&mut self, _buffer: &mut [u8]) -> std::io::Result<usize> {
            std::thread::sleep(Duration::from_secs(2));
            Ok(0)
        }
    }

    #[test]
    fn wait_for_ready_times_out_when_the_server_stays_silent() {
        let lines = BufReader::new(Stalled);
        assert_eq!(
            wait_for_ready(lines, Duration::from_millis(100)),
            Err(ServerError::Timeout)
        );
    }

    #[test]
    fn errors_have_a_stable_code_for_the_screen() {
        assert_eq!(ServerError::Spawn.code(), "server_spawn_failed");
        assert_eq!(ServerError::Timeout.code(), "server_timeout");
        assert_eq!(ServerError::Exited.code(), "server_exited");
    }
}
