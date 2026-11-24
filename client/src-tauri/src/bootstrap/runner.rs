//! El ejecutor real de la preparación (spec 022): cada comando sin consola, con su salida en `bootstrap.log`.

use std::ffi::OsString;
use std::path::{Path, PathBuf};

use super::prepare::Runner;

/// Corre cada comando sin consola y agrega su salida a `bootstrap.log`.
pub struct CommandRunner {
    pub log: PathBuf,
}

impl Runner for CommandRunner {
    fn run(
        &mut self,
        program: &Path,
        args: &[OsString],
        env: &[(&'static str, OsString)],
    ) -> Result<(), String> {
        use std::io::Write;
        if let Some(folder) = self.log.parent() {
            std::fs::create_dir_all(folder).map_err(|error| error.to_string())?;
        }
        let mut file = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.log)
            .map_err(|error| error.to_string())?;
        let _ = writeln!(file, "> {} {:?}", program.display(), args);
        let mut command = std::process::Command::new(program);
        command
            .args(args)
            .envs(env.iter().map(|(key, value)| (*key, value)))
            .stdin(std::process::Stdio::null())
            .stdout(file.try_clone().map_err(|error| error.to_string())?)
            .stderr(file.try_clone().map_err(|error| error.to_string())?);
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            command.creation_flags(0x0800_0000); // CREATE_NO_WINDOW
        }
        let status = command.status().map_err(|error| error.to_string())?;
        if status.success() {
            Ok(())
        } else {
            let _ = writeln!(file, "< exit {:?}", status.code());
            Err(format!("exit {:?}", status.code()))
        }
    }
}
