from nirikshak._runtime import ensure_static_tls

ensure_static_tls()  # must run before qiskit_aer and sklearn are both loaded (Linux)
