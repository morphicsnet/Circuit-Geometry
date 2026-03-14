fn main() {
    let proto_path = "../../proto/sidecar.proto";
    let protoc = protoc_bin_vendored::protoc_bin_path().expect("failed to locate protoc");
    std::env::set_var("PROTOC", protoc);
    println!("cargo:rerun-if-changed={proto_path}");
    tonic_build::configure()
        .build_client(false)
        .compile_protos(&[proto_path], &["../../proto"])
        .expect("failed to compile sidecar proto");
}
