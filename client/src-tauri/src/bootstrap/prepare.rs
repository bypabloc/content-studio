//! La preparación de la app instalada (spec 022, D-2): Python, el venv del server y la siembra, con uv.
// cspell:ignore LOCALAPPDATA

use std::ffi::OsString;
use std::path::{Path, PathBuf};

use serde::Serialize;

use super::Mode;

/// Versión de Python del venv de la app.
pub const PYTHON: &str = "3.12";

/// Las carpetas de la app instalada: los datos (`%LOCALAPPDATA%\Content Studio`, o `CONTENT_STUDIO_HOME`, igual que
/// `paths.data_dir()` del server), los recursos empaquetados y la versión de la app.
#[derive(Debug, Clone)]
pub struct Layout {
    pub home: PathBuf,
    pub resources: PathBuf,
    pub version: String,
}

impl Layout {
    pub fn from_env(resources: PathBuf, version: &str) -> Self {
        let home = std::env::var_os("CONTENT_STUDIO_HOME")
            .map(PathBuf::from)
            .unwrap_or_else(|| {
                let local = std::env::var_os("LOCALAPPDATA")
                    .map(PathBuf::from)
                    .unwrap_or_default();
                local.join("Content Studio")
            });
        Layout {
            home,
            resources,
            version: version.to_string(),
        }
    }

    pub fn uv(&self) -> PathBuf {
        self.resources
            .join("bin")
            .join(if cfg!(windows) { "uv.exe" } else { "uv" })
    }

    pub fn venv(&self) -> PathBuf {
        self.home.join("venv")
    }

    /// El `studio` del venv de la app, con el que arranca el server.
    pub fn studio(&self) -> PathBuf {
        if cfg!(windows) {
            self.venv().join("Scripts").join("studio.exe")
        } else {
            self.venv().join("bin").join("studio")
        }
    }

    pub fn log(&self) -> PathBuf {
        self.home.join("logs").join("bootstrap.log")
    }

    fn marker(&self) -> PathBuf {
        self.venv().join(".app-version")
    }

    fn uv_env(&self) -> Vec<(&'static str, OsString)> {
        vec![
            (
                "UV_PYTHON_INSTALL_DIR",
                self.home.join("python").into_os_string(),
            ),
            ("UV_PROJECT_ENVIRONMENT", self.venv().into_os_string()),
            ("UV_CACHE_DIR", self.home.join("uv-cache").into_os_string()),
            ("UV_PYTHON_PREFERENCE", OsString::from("only-managed")),
        ]
    }
}

/// Un aviso de progreso para la pantalla de preparación: el paso, su estado y dónde está el log.
#[derive(Serialize, Clone, Debug, PartialEq, Eq)]
pub struct Progress {
    pub step: &'static str,
    pub state: &'static str,
    pub log: String,
}

/// Quien corre los comandos de la preparación; las pruebas lo simulan.
pub trait Runner {
    fn run(
        &mut self,
        program: &Path,
        args: &[OsString],
        env: &[(&'static str, OsString)],
    ) -> Result<(), String>;
}

/// Prepara Python, el venv del server y los datos de la app. Con el venv ya hecho para esta versión
/// (`venv/.app-version`), solo siembra: no repite pasos ni necesita internet. Un error devuelve su código.
pub fn prepare(
    layout: &Layout,
    runner: &mut impl Runner,
    emit: &mut impl FnMut(Progress),
) -> Result<(), &'static str> {
    let log = layout.log().display().to_string();
    let mut report = |step: &'static str, state: &'static str| {
        emit(Progress {
            step,
            state,
            log: log.clone(),
        })
    };
    let uv = layout.uv();
    let env = layout.uv_env();
    let ready =
        std::fs::read_to_string(layout.marker()).is_ok_and(|done| done.trim() == layout.version);
    if ready {
        report("python", "skipped");
        report("sync", "skipped");
    } else {
        report("python", "running");
        let python: Vec<OsString> = ["python", "install", PYTHON].map(OsString::from).to_vec();
        runner.run(&uv, &python, &env).map_err(|_| {
            report("python", "failed");
            "bootstrap_python_failed"
        })?;
        report("python", "done");
        report("sync", "running");
        let mut sync: Vec<OsString> = [
            "sync",
            "--frozen",
            "--no-dev",
            "--package",
            "content-studio",
            "--python",
            PYTHON,
            "--project",
        ]
        .map(OsString::from)
        .to_vec();
        sync.push(layout.resources.join("app").into_os_string());
        runner
            .run(&uv, &sync, &env)
            .and_then(|()| {
                std::fs::write(layout.marker(), &layout.version).map_err(|error| error.to_string())
            })
            .map_err(|_| {
                report("sync", "failed");
                "bootstrap_sync_failed"
            })?;
        report("sync", "done");
    }
    report("seed", "running");
    let seed_env = Mode::Installed {
        resources: layout.resources.clone(),
    }
    .server_env();
    runner
        .run(&layout.studio(), &[OsString::from("seed")], &seed_env)
        .map_err(|_| {
            report("seed", "failed");
            "bootstrap_seed_failed"
        })?;
    report("seed", "done");
    Ok(())
}

#[cfg(test)]
#[path = "prepare_tests.rs"]
mod tests;
