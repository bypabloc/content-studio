fn main() {
    // La carpeta del perfil (target/<perfil>): el ejecutable que corre desde ahí es de desarrollo (spec 022, D-2).
    let out = std::path::PathBuf::from(std::env::var("OUT_DIR").expect("cargo define OUT_DIR"));
    let profile = out
        .ancestors()
        .nth(3)
        .expect("OUT_DIR está en target/<perfil>/build/<paquete>/out");
    println!(
        "cargo:rustc-env=CONTENT_STUDIO_BUILD_DIR={}",
        profile.display()
    );
    tauri_build::build()
}
