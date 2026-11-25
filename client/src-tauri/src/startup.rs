//! Inicio con Windows (spec 031, D-4, AC-8): el valor `Run` de HKCU arranca el server con la sesión, sin admin.

use std::ffi::OsStr;
use std::iter::once;
use std::os::windows::ffi::OsStrExt;
use std::path::Path;

use windows::core::{w, PCWSTR};
use windows::Win32::Foundation::{ERROR_FILE_NOT_FOUND, ERROR_SUCCESS, WIN32_ERROR};
use windows::Win32::System::Registry::{RegDeleteKeyValueW, RegSetKeyValueW, HKEY_CURRENT_USER, REG_SZ};

/// El nombre del valor en `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
pub const VALUE_NAME: &str = "ContentStudioServer";

const RUN_KEY: PCWSTR = w!("Software\\Microsoft\\Windows\\CurrentVersion\\Run");

/// Dónde se guarda el inicio. El real es el registro; las pruebas usan un mapa en memoria.
pub trait RunKey {
    fn set(&mut self, name: &str, command: &str) -> Result<(), String>;
    fn remove(&mut self, name: &str) -> Result<(), String>;
}

/// Activa o desactiva el inicio con Windows (AC-8): el valor existe mientras esté activo.
pub fn apply(key: &mut dyn RunKey, enabled: bool, command: &str) -> Result<(), String> {
    if enabled {
        key.set(VALUE_NAME, command)
    } else {
        key.remove(VALUE_NAME)
    }
}

/// El comando del inicio: el `pythonw.exe` del venv del server, sin ventana.
pub fn server_command(venv: &Path) -> String {
    format!("\"{}\" -m content_studio api up", venv.join("Scripts").join("pythonw.exe").display())
}

/// La clave `Run` del usuario actual: no pide admin.
pub struct CurrentUserRun;

impl RunKey for CurrentUserRun {
    fn set(&mut self, name: &str, command: &str) -> Result<(), String> {
        let value = wide(name);
        let data = wide(command);
        // SAFETY: los punteros apuntan a búferes UTF-16 con su terminador nulo y vivos durante la llamada.
        let status = unsafe {
            RegSetKeyValueW(
                HKEY_CURRENT_USER,
                RUN_KEY,
                PCWSTR(value.as_ptr()),
                REG_SZ.0,
                Some(data.as_ptr().cast()),
                (data.len() * 2) as u32,
            )
        };
        check(status)
    }

    fn remove(&mut self, name: &str) -> Result<(), String> {
        let value = wide(name);
        // SAFETY: `value` es un búfer UTF-16 con terminador nulo que vive durante la llamada.
        let status = unsafe { RegDeleteKeyValueW(HKEY_CURRENT_USER, RUN_KEY, PCWSTR(value.as_ptr())) };
        if status == ERROR_FILE_NOT_FOUND {
            return Ok(());
        }
        check(status)
    }
}

fn wide(text: &str) -> Vec<u16> {
    OsStr::new(text).encode_wide().chain(once(0)).collect()
}

fn check(status: WIN32_ERROR) -> Result<(), String> {
    if status == ERROR_SUCCESS {
        Ok(())
    } else {
        Err(format!("registro: error {}", status.0))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;
    use std::path::Path;

    #[derive(Default)]
    struct FakeRun(HashMap<String, String>);

    impl RunKey for FakeRun {
        fn set(&mut self, name: &str, command: &str) -> Result<(), String> {
            self.0.insert(name.to_string(), command.to_string());
            Ok(())
        }

        fn remove(&mut self, name: &str) -> Result<(), String> {
            self.0.remove(name);
            Ok(())
        }
    }

    #[test]
    fn writes_and_removes_run_value() {
        let mut run = FakeRun::default();
        let command = server_command(Path::new(r"C:\app\.venv"));
        apply(&mut run, true, &command).unwrap();
        assert_eq!(
            run.0.get(VALUE_NAME).map(String::as_str),
            Some(r#""C:\app\.venv\Scripts\pythonw.exe" -m content_studio api up"#)
        );
        apply(&mut run, false, &command).unwrap();
        assert!(!run.0.contains_key(VALUE_NAME));
    }
}
