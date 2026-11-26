//! Regla de firewall de la red local (spec 032, D-5, AC-9): solo para el perfil Privado, creada con `netsh` elevado.
//! El instalador es por usuario y sin admin, así que Windows pide elevación (UAC) al activar y al desactivar.

/// El nombre de la regla de entrada en el Firewall de Windows.
pub const RULE_NAME: &str = "Content Studio LAN";

/// El error que ve la app si el usuario rechaza el aviso de UAC.
pub const DECLINED: &str = "firewall_declined";

/// Cómo terminó el programa elevado.
#[derive(Debug, PartialEq, Eq)]
pub enum Elevated {
    Done(u32),
    Declined,
}

/// Quién corre el comando con elevación. El real es `ShellExecuteExW` con `runas`; las pruebas lo simulan.
pub trait Elevate {
    fn run(&mut self, program: &str, params: &str) -> Result<Elevated, String>;
}

/// El programa y sus parámetros: activar borra la regla vieja y crea la nueva en una sola elevación.
pub fn rule_command(enabled: bool, port: u16) -> (String, String) {
    let delete = format!("advfirewall firewall delete rule name=\"{RULE_NAME}\"");
    if !enabled {
        return ("netsh.exe".to_string(), delete);
    }
    let add = format!(
        "advfirewall firewall add rule name=\"{RULE_NAME}\" dir=in action=allow protocol=TCP localport={port} profile=private"
    );
    ("cmd.exe".to_string(), format!("/c netsh {delete} >nul & netsh {add}"))
}

/// Crea o borra la regla (AC-9). Borrar una regla que no existe no es un error.
pub fn apply(elevate: &mut dyn Elevate, enabled: bool, port: u16) -> Result<(), String> {
    let (program, params) = rule_command(enabled, port);
    match elevate.run(&program, &params)? {
        Elevated::Declined => Err(DECLINED.to_string()),
        Elevated::Done(0) => Ok(()),
        Elevated::Done(_) if !enabled => Ok(()),
        Elevated::Done(code) => Err(format!("netsh: exit {code}")),
    }
}

/// `ShellExecuteExW` con el verbo `runas`: muestra el aviso de UAC y espera a que termine el programa.
pub struct RunAs;

impl Elevate for RunAs {
    fn run(&mut self, program: &str, params: &str) -> Result<Elevated, String> {
        use std::ffi::OsStr;
        use std::iter::once;
        use std::os::windows::ffi::OsStrExt;

        use windows::core::{w, HRESULT, PCWSTR};
        use windows::Win32::Foundation::{CloseHandle, ERROR_CANCELLED};
        use windows::Win32::System::Threading::{GetExitCodeProcess, WaitForSingleObject, INFINITE};
        use windows::Win32::UI::Shell::{ShellExecuteExW, SEE_MASK_NOCLOSEPROCESS, SHELLEXECUTEINFOW};
        use windows::Win32::UI::WindowsAndMessaging::SW_HIDE;

        let wide = |text: &str| -> Vec<u16> { OsStr::new(text).encode_wide().chain(once(0)).collect() };
        let file = wide(program);
        let parameters = wide(params);
        let mut info = SHELLEXECUTEINFOW {
            cbSize: std::mem::size_of::<SHELLEXECUTEINFOW>() as u32,
            fMask: SEE_MASK_NOCLOSEPROCESS,
            lpVerb: w!("runas"),
            lpFile: PCWSTR(file.as_ptr()),
            lpParameters: PCWSTR(parameters.as_ptr()),
            nShow: SW_HIDE.0,
            ..Default::default()
        };
        // SAFETY: `info` y los búferes UTF-16 que apunta viven durante la llamada.
        if let Err(error) = unsafe { ShellExecuteExW(&mut info) } {
            if error.code() == HRESULT::from_win32(ERROR_CANCELLED.0) {
                return Ok(Elevated::Declined);
            }
            return Err(error.message());
        }
        let mut code = 0u32;
        // SAFETY: con SEE_MASK_NOCLOSEPROCESS, `hProcess` es un handle válido que se cierra aquí mismo.
        unsafe {
            WaitForSingleObject(info.hProcess, INFINITE);
            let status = GetExitCodeProcess(info.hProcess, &mut code);
            let _ = CloseHandle(info.hProcess);
            status.map_err(|error| error.message())?;
        }
        Ok(Elevated::Done(code))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    struct Fake {
        result: Elevated,
        calls: Vec<(String, String)>,
    }

    impl Elevate for Fake {
        fn run(&mut self, program: &str, params: &str) -> Result<Elevated, String> {
            self.calls.push((program.to_string(), params.to_string()));
            Ok(std::mem::replace(&mut self.result, Elevated::Done(0)))
        }
    }

    #[test]
    fn builds_private_profile_rule() {
        let (program, params) = rule_command(true, 41831);
        assert_eq!(program, "cmd.exe");
        assert!(params.contains("profile=private"));
        assert!(params.contains("localport=41831"));
        assert!(params.contains("dir=in"));
        assert!(params.contains(RULE_NAME));
        let mut declined = Fake { result: Elevated::Declined, calls: vec![] };
        assert_eq!(apply(&mut declined, true, 41831), Err(DECLINED.to_string()));
    }

    #[test]
    fn disabling_deletes_the_rule_even_if_it_was_missing() {
        let mut missing = Fake { result: Elevated::Done(1), calls: vec![] };
        assert_eq!(apply(&mut missing, false, 41831), Ok(()));
        assert_eq!(missing.calls[0].0, "netsh.exe");
        assert!(missing.calls[0].1.contains("delete rule"));
        assert!(!missing.calls[0].1.contains("add rule"));
    }

    #[test]
    fn a_failed_add_is_an_error() {
        let mut failed = Fake { result: Elevated::Done(1), calls: vec![] };
        assert_eq!(apply(&mut failed, true, 41831), Err("netsh: exit 1".to_string()));
    }
}
