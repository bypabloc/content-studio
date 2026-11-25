//! Primer arranque de la app instalada (spec 022, D-2): el modo (checkout o instalada) y los pasos con uv.

use std::ffi::OsString;
use std::path::{Path, PathBuf};

mod prepare;
mod runner;

pub use prepare::{prepare, Layout, Progress};
pub use runner::CommandRunner;

/// Dónde corre la app: en un checkout (desarrollo) o instalada, con sus recursos empaquetados.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Mode {
    Dev { checkout: PathBuf },
    Installed { resources: PathBuf },
}

/// Instalada si el ejecutable no está dentro del checkout donde se compiló ni en su carpeta de build.
/// La carpeta de build cuenta aparte porque los worktrees comparten el target de Cargo fuera del checkout.
pub fn detect_mode(exe: &Path, checkout: &Path, build: &Path, resources: &Path) -> Mode {
    if exe.starts_with(checkout) || exe.starts_with(build) {
        Mode::Dev {
            checkout: checkout.to_path_buf(),
        }
    } else {
        Mode::Installed {
            resources: resources.to_path_buf(),
        }
    }
}

/// El modo de este ejecutable: compara su ruta real con el checkout y el build donde se compiló.
pub fn current_mode(resources: PathBuf) -> Mode {
    let real = |path: PathBuf| path.canonicalize().unwrap_or(path);
    let checkout = real(
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("..")
            .join(".."),
    );
    let build = real(PathBuf::from(env!("CONTENT_STUDIO_BUILD_DIR")));
    let exe = std::env::current_exe().map(real).unwrap_or_default();
    detect_mode(&exe, &checkout, &build, &resources)
}

impl Mode {
    /// Variables para el server: en la app instalada, el modo y la carpeta de recursos.
    pub fn server_env(&self) -> Vec<(&'static str, OsString)> {
        match self {
            Mode::Dev { .. } => Vec::new(),
            Mode::Installed { resources } => vec![
                ("CONTENT_STUDIO_MODE", OsString::from("installed")),
                (
                    "CONTENT_STUDIO_RESOURCES",
                    resources.clone().into_os_string(),
                ),
            ],
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn paths() -> (PathBuf, PathBuf, PathBuf) {
        (
            PathBuf::from("/repo/content-studio"),
            PathBuf::from("/repo/tmp/cargo-target/debug"),
            PathBuf::from("/apps/Content Studio"),
        )
    }

    #[test]
    fn detect_mode_is_dev_inside_the_checkout_or_its_build_folder() {
        let (checkout, build, resources) = paths();
        let in_checkout = checkout.join("client/src-tauri/target/debug/content-studio.exe");
        let in_build = build.join("content-studio.exe");
        assert_eq!(
            detect_mode(&in_checkout, &checkout, &build, &resources),
            Mode::Dev {
                checkout: checkout.clone()
            }
        );
        assert_eq!(
            detect_mode(&in_build, &checkout, &build, &resources),
            Mode::Dev {
                checkout: checkout.clone()
            }
        );
    }

    #[test]
    fn detect_mode_is_installed_anywhere_else() {
        let (checkout, build, resources) = paths();
        let exe = resources.join("content-studio.exe");
        assert_eq!(
            detect_mode(&exe, &checkout, &build, &resources),
            Mode::Installed {
                resources: resources.clone()
            }
        );
    }

    #[test]
    fn only_the_installed_app_tells_the_server_its_mode_and_resources() {
        let (checkout, _, resources) = paths();
        assert!(Mode::Dev { checkout }.server_env().is_empty());
        let installed = Mode::Installed {
            resources: resources.clone(),
        }
        .server_env();
        assert_eq!(
            installed[0],
            ("CONTENT_STUDIO_MODE", OsString::from("installed"))
        );
        assert_eq!(
            installed[1],
            ("CONTENT_STUDIO_RESOURCES", resources.into_os_string())
        );
    }
}

/// El venv de la app instalada, donde está el `pythonw.exe` del inicio con Windows (spec 031, AC-8). En el checkout no hay.
pub fn installed_venv(mode: &Mode, version: &str) -> Option<PathBuf> {
    match mode {
        Mode::Installed { resources } => Some(prepare::Layout::from_env(resources.clone(), version).venv()),
        Mode::Dev { .. } => None,
    }
}
