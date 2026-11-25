//! Pruebas de la ventana (spec 028): arranque, cambio de versión, cambio de token y apagado, con un `studio` falso.

use super::*;

const READY_0_1_0: &str = r#"{"ready": {"url": "http://127.0.0.1:41830", "port": 41830, "pid": 7, "version": "0.1.0", "token": "t1"}}"#;
const READY_0_2_0: &str = r#"{"ready": {"url": "http://127.0.0.1:41830", "port": 41830, "pid": 9, "version": "0.2.0", "token": "t2"}}"#;

fn answer(stdout: &str) -> server::Run {
    server::Run {
        success: true,
        stdout: stdout.to_string(),
    }
}

#[test]
fn connect_attaches_to_running_server() {
    let mut calls: Vec<String> = Vec::new();
    let connection = attach(
        &mut |args| {
            calls.push(args.join(" "));
            Ok(answer(READY_0_1_0))
        },
        "0.1.0",
    )
    .expect("la ventana se adjunta al server que responde");
    assert_eq!(connection.base_url, "http://127.0.0.1:41830");
    assert_eq!(connection.token, "t1");
    assert_eq!(calls, vec!["api up --with-token"]);
}

#[test]
fn restarts_server_of_other_version() {
    let mut calls: Vec<String> = Vec::new();
    let mut answers = vec![answer(READY_0_1_0), answer(""), answer(READY_0_2_0)].into_iter();
    let connection = attach(
        &mut |args| {
            calls.push(args.join(" "));
            Ok(answers.next().expect("una respuesta por llamada"))
        },
        "0.2.0",
    )
    .expect("el server de otra versión se reemplaza");
    assert_eq!(
        calls,
        vec!["api up --with-token", "api down", "api up --with-token"]
    );
    assert_eq!(connection.token, "t2");
}

#[test]
fn stop_asks_for_force() {
    let mut calls: Vec<String> = Vec::new();
    stop(&mut |args| {
        calls.push(args.join(" "));
        Ok(answer(""))
    })
    .expect("el server se detiene");
    assert_eq!(calls, vec!["api down --force"]);
}

#[test]
fn stop_fails_when_studio_refuses() {
    let result = stop(&mut |_| {
        Ok(server::Run {
            success: false,
            stdout: String::new(),
        })
    });
    assert_eq!(result.err(), Some(ServerError::Exited));
}

#[test]
fn rotate_stops_the_server_then_changes_the_token() {
    let mut calls: Vec<String> = Vec::new();
    rotate(&mut |args| {
        calls.push(args.join(" "));
        Ok(answer(""))
    })
    .expect("el token cambia con el server detenido");
    assert_eq!(calls, vec!["api down", "api token --rotate"]);
}

#[test]
fn rotate_keeps_the_token_while_jobs_run() {
    let mut calls: Vec<String> = Vec::new();
    let result = rotate(&mut |args| {
        calls.push(args.join(" "));
        Ok(server::Run {
            success: false,
            stdout: String::new(),
        })
    });
    assert_eq!(result.err(), Some(ServerError::Exited));
    assert_eq!(calls, vec!["api down"]);
}

#[test]
fn a_failing_up_is_reported_as_exited() {
    let result = attach(
        &mut |_| {
            Ok(server::Run {
                success: false,
                stdout: String::new(),
            })
        },
        "0.1.0",
    );
    assert_eq!(result.err(), Some(ServerError::Exited));
}
