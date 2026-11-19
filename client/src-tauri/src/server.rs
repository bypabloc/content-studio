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
        // Una línea que no es UTF-8 se salta: cortar aquí dejaría el pipe sin leer, y el server fallaría al escribir.
        for line in lines.lines().filter_map(Result::ok) {
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

/// `uv run --project <raíz> studio serve --port 0 --token <t>`, sin consola en Windows y suspendido hasta `job::resume`.
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
        command.creation_flags(CREATE_NO_WINDOW | CREATE_SUSPENDED);
    }
    command.spawn().map_err(|_| ServerError::Spawn)
}

#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x0800_0000;

/// El proceso nace suspendido: así el Job lo recibe antes de que cree sus hijos (uv → studio → python).
#[cfg(windows)]
const CREATE_SUSPENDED: u32 = 0x0000_0004;

// cspell:ignore Toolhelp SNAPTHREAD THREADENTRY ascii
/// Un Job Object con KILL_ON_JOB_CLOSE: el server muere con la ventana aunque la app se cierre mal (D-2).
#[cfg(windows)]
pub mod job {
    use std::os::windows::io::AsRawHandle;
    use std::process::Child;

    use windows::Win32::Foundation::{CloseHandle, HANDLE};
    use windows::Win32::System::Diagnostics::ToolHelp::{
        CreateToolhelp32Snapshot, Thread32First, Thread32Next, TH32CS_SNAPTHREAD, THREADENTRY32,
    };
    use windows::Win32::System::JobObjects::{
        AssignProcessToJobObject, CreateJobObjectW, JobObjectExtendedLimitInformation,
        SetInformationJobObject, JOBOBJECT_EXTENDED_LIMIT_INFORMATION,
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    };
    use windows::Win32::System::Threading::{OpenThread, ResumeThread, THREAD_SUSPEND_RESUME};

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
                // Desde aquí, el Drop cierra el handle si un `?` de abajo sale antes del Ok.
                let owned = Self(job);
                let size = std::mem::size_of::<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>() as u32;
                SetInformationJobObject(
                    job,
                    JobObjectExtendedLimitInformation,
                    &info as *const _ as *const _,
                    size,
                )?;
                AssignProcessToJobObject(job, HANDLE(child.as_raw_handle()))?;
                Ok(owned)
            }
        }
    }

    /// Pone en marcha los hilos de un proceso que arrancó suspendido, ya dentro del Job.
    pub fn resume(child: &Child) -> windows::core::Result<()> {
        let pid = child.id();
        unsafe {
            let snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)?;
            let result = resume_threads(snapshot, pid);
            CloseHandle(snapshot)?;
            result
        }
    }

    /// Reanuda cada hilo de `pid` que aparece en la instantánea de hilos.
    unsafe fn resume_threads(snapshot: HANDLE, pid: u32) -> windows::core::Result<()> {
        let mut entry = THREADENTRY32 {
            dwSize: std::mem::size_of::<THREADENTRY32>() as u32,
            ..Default::default()
        };
        let mut more = Thread32First(snapshot, &mut entry).is_ok();
        while more {
            if entry.th32OwnerProcessID == pid {
                let thread = OpenThread(THREAD_SUSPEND_RESUME, false, entry.th32ThreadID)?;
                let previous = ResumeThread(thread);
                let _ = CloseHandle(thread);
                if previous == u32::MAX {
                    return Err(windows::core::Error::from_thread());
                }
            }
            more = Thread32Next(snapshot, &mut entry).is_ok();
        }
        Ok(())
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

    /// Al cerrar el Job tienen que morir `cmd` y el `ping` que lanza (el nieto). Solo funciona si el Job recibe el
    /// proceso suspendido, antes de que cree sus hijos (en la app: uv → studio → python).
    #[cfg(windows)]
    #[test]
    fn job_closing_takes_the_grandchildren_too() {
        use std::os::windows::process::CommandExt;
        let mut child = std::process::Command::new("cmd")
            .args(["/C", "ping -n 300 127.0.0.1 > NUL"])
            .creation_flags(CREATE_SUSPENDED | CREATE_NO_WINDOW)
            .spawn()
            .expect("cmd debe arrancar");
        let job = job::KillOnClose::assign(&child).expect("el Job recibe el proceso suspendido");
        job::resume(&child).expect("el proceso se reanuda dentro del Job");
        let ping = poll_until(|| child_named(child.id(), "ping.exe")).expect("cmd debe lanzar su ping");
        drop(job);
        // Sondeo acotado: si el Job no mata a cmd, la prueba falla en 10 s en vez de esperar los 300 de ping.
        poll_until(|| child.try_wait().ok().flatten()).expect("cmd termina al cerrar el Job");
        assert!(!is_alive(ping), "el ping (nieto) debe morir con el Job");
    }

    /// Sondeo acotado (10 s) de un estado real del sistema; sin tiempo fijo.
    #[cfg(windows)]
    fn poll_until<T>(mut probe: impl FnMut() -> Option<T>) -> Option<T> {
        for _ in 0..20 {
            if let Some(value) = probe() {
                return Some(value);
            }
            std::thread::sleep(Duration::from_millis(500));
        }
        None
    }

    /// PID del hijo de `parent` cuyo nombre de imagen es `image`, según WMI.
    #[cfg(windows)]
    fn child_named(parent: u32, image: &str) -> Option<u32> {
        let script = format!(
            "Get-CimInstance Win32_Process -Filter 'ParentProcessId={parent}' | ForEach-Object {{ \"$($_.ProcessId) $($_.Name)\" }}"
        );
        let out = std::process::Command::new("powershell")
            .args(["-NoProfile", "-Command", &script])
            .output()
            .ok()?;
        String::from_utf8_lossy(&out.stdout)
            .lines()
            .filter_map(|line| line.split_once(' '))
            .find(|(_, name)| name.trim().eq_ignore_ascii_case(image))
            .and_then(|(pid, _)| pid.parse().ok())
    }

    /// Si el proceso `pid` sigue vivo. Un fallo de PowerShell corta la prueba: no puede contar como "muerto".
    #[cfg(windows)]
    fn is_alive(pid: u32) -> bool {
        let script = format!("if (Get-Process -Id {pid} -ErrorAction SilentlyContinue) {{ 'vivo' }}");
        let out = std::process::Command::new("powershell")
            .args(["-NoProfile", "-Command", &script])
            .output()
            .expect("PowerShell debe arrancar para consultar el proceso");
        assert!(out.status.success(), "PowerShell falló: {}", String::from_utf8_lossy(&out.stderr));
        String::from_utf8_lossy(&out.stdout).contains("vivo")
    }
}
