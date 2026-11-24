//! Pruebas de la preparación (spec 022, AC-5) con un ejecutor simulado.

use super::*;

/// Un ejecutor simulado: anota cada comando (programa y primer argumento) y falla una vez en el paso pedido.
struct Fake {
    calls: Vec<String>,
    fail_once: Option<&'static str>,
}

impl Runner for Fake {
    fn run(
        &mut self,
        program: &Path,
        args: &[OsString],
        _env: &[(&'static str, OsString)],
    ) -> Result<(), String> {
        let name = program.file_stem().unwrap().to_string_lossy().to_string();
        let first = args[0].to_string_lossy().to_string();
        self.calls.push(format!("{name} {first}"));
        if self.fail_once == Some(first.as_str()) {
            self.fail_once = None;
            return Err("exit Some(1)".into());
        }
        Ok(())
    }
}

fn layout(name: &str) -> Layout {
    let home = std::env::temp_dir().join(format!(
        "content-studio-bootstrap-{name}-{}",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&home);
    std::fs::create_dir_all(home.join("venv")).unwrap();
    Layout {
        home: home.clone(),
        resources: home.join("resources"),
        version: "0.1.0".into(),
    }
}

#[test]
fn the_first_run_installs_python_syncs_the_venv_seeds_and_marks_the_version() {
    let layout = layout("first");
    let mut runner = Fake {
        calls: Vec::new(),
        fail_once: None,
    };
    let mut events = Vec::new();

    assert_eq!(
        prepare(&layout, &mut runner, &mut |event| events
            .push((event.step, event.state))),
        Ok(())
    );

    assert_eq!(runner.calls, ["uv python", "uv sync", "studio seed"]);
    assert_eq!(
        std::fs::read_to_string(layout.venv().join(".app-version")).unwrap(),
        "0.1.0"
    );
    assert_eq!(
        events,
        [
            ("python", "running"),
            ("python", "done"),
            ("sync", "running"),
            ("sync", "done"),
            ("seed", "running"),
            ("seed", "done")
        ]
    );
}

#[test]
fn a_failed_sync_stops_with_its_code_and_the_retry_does_not_repeat_finished_steps() {
    let layout = layout("retry");
    let mut runner = Fake {
        calls: Vec::new(),
        fail_once: Some("sync"),
    };
    let mut events = Vec::new();

    assert_eq!(
        prepare(&layout, &mut runner, &mut |event| events.push(event)),
        Err("bootstrap_sync_failed")
    );
    assert_eq!(runner.calls, ["uv python", "uv sync"]);
    let last = events.last().unwrap();
    assert_eq!((last.step, last.state), ("sync", "failed"));
    assert!(last.log.ends_with("bootstrap.log"));
    assert!(!layout.venv().join(".app-version").exists());

    assert_eq!(prepare(&layout, &mut runner, &mut |_| ()), Ok(()));
    runner.calls.clear();
    let mut states = Vec::new();
    assert_eq!(
        prepare(&layout, &mut runner, &mut |event| states
            .push((event.step, event.state))),
        Ok(())
    );
    assert_eq!(runner.calls, ["studio seed"]);
    assert_eq!(states[..2], [("python", "skipped"), ("sync", "skipped")]);
}

#[test]
fn a_new_app_version_syncs_the_venv_again() {
    let layout = layout("upgrade");
    std::fs::write(layout.venv().join(".app-version"), "0.0.9").unwrap();
    let mut runner = Fake {
        calls: Vec::new(),
        fail_once: None,
    };

    assert_eq!(prepare(&layout, &mut runner, &mut |_| ()), Ok(()));
    assert_eq!(runner.calls, ["uv python", "uv sync", "studio seed"]);
}

#[test]
fn the_layout_follows_the_data_folder_of_the_server() {
    let layout = Layout {
        home: PathBuf::from("/home/cs"),
        resources: PathBuf::from("/res"),
        version: "1".into(),
    };
    assert_eq!(layout.log(), PathBuf::from("/home/cs/logs/bootstrap.log"));
    assert!(layout.uv().starts_with("/res/bin"));
    assert!(layout.studio().starts_with("/home/cs/venv"));
}
