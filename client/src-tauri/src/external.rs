//! Enlaces `content-studio://` y «Enviar a» (spec 031, D-1): reenvía el `argv` de un arranque a la ventana. Rust no
//! lo interpreta: la lista blanca es de `parseExternal` (client/src/app/external/parseExternal.ts).

use std::path::Path;

/// El evento con el que la ventana recibe el `argv`.
pub const EVENT: &str = "external-request";

/// Entrega el `argv` a la ventana por `emit` (AC-5).
pub fn forward_argv(argv: &[String], mut emit: impl FnMut(&[String])) {
    emit(argv);
}

/// El `argv` con el que arrancó este proceso: un enlace que abre la app en frío llega aquí (AC-1).
#[tauri::command]
pub fn startup_argv() -> Vec<String> {
    std::env::args().collect()
}

/// Si una ruta de un enlace es un archivo que existe. Un enlace nunca ejecuta la ruta: solo rellena (AC-4).
#[tauri::command]
pub fn path_exists(path: String) -> bool {
    Path::new(&path).is_file()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn forwards_argv_to_window() {
        let argv = vec!["content-studio.exe".to_string(), "content-studio://open/music".to_string()];
        let mut sent: Vec<String> = Vec::new();
        forward_argv(&argv, |payload| sent = payload.to_vec());
        assert_eq!(sent, argv);
    }

    #[test]
    fn path_exists_is_true_only_for_files() {
        let dir = env!("CARGO_MANIFEST_DIR");
        assert!(path_exists(format!("{dir}/Cargo.toml")));
        assert!(!path_exists(dir.to_string()));
        assert!(!path_exists(format!("{dir}/no-such-file.wav")));
    }

    #[test]
    fn startup_argv_is_this_process_argv() {
        assert_eq!(startup_argv(), std::env::args().collect::<Vec<_>>());
    }
}
