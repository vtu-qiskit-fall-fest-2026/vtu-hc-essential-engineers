import os
import subprocess
import sys

import pytest


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="libgomp TLS clash is Linux-only")
def test_aer_and_sklearn_load_together_without_preset_tunable():
    env = {k: v for k, v in os.environ.items() if k not in ("GLIBC_TUNABLES", "NIRIKSHAK_NO_REEXEC")}
    code = "import nirikshak, qiskit_aer, sklearn.ensemble, xgboost; print('ok')"
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-500:]
    assert out.stdout.strip() == "ok"
