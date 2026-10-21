"""Linux workaround for the libgomp static TLS clash.

qiskit-aer and scikit-learn (and xgboost) each bundle their own libgomp. Loaded into one
process on Linux they exhaust glibc's static TLS surplus and the second import fails with
"cannot allocate memory in static TLS block". Import order does not help (verified on
x86_64, Ubuntu glibc 2.39). The fix is the glibc tunable below, which glibc only reads at
process start, so if it is missing we restart the same command once with it set.

Set NIRIKSHAK_NO_REEXEC=1 to disable the restart.
"""

from __future__ import annotations

import os
import sys
import warnings

TUNABLE = "glibc.rtld.optional_static_tls=4096"


def ensure_static_tls() -> None:
    if not sys.platform.startswith("linux"):
        return
    current = os.environ.get("GLIBC_TUNABLES", "")
    if "glibc.rtld.optional_static_tls" in current or os.environ.get("NIRIKSHAK_NO_REEXEC"):
        return
    # Interactive sessions, notebooks and stdin scripts cannot be restarted transparently.
    if (hasattr(sys, "ps1") or sys.flags.interactive or "ipykernel" in sys.modules
            or sys.argv[0] in ("", "-")):
        warnings.warn(
            "nirikshak: qiskit-aer and scikit-learn may fail to load together "
            "('cannot allocate memory in static TLS block'). Start Python with "
            f"GLIBC_TUNABLES={TUNABLE} set.", RuntimeWarning, stacklevel=3)
        return
    os.environ["GLIBC_TUNABLES"] = f"{current}:{TUNABLE}" if current else TUNABLE
    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(sys.executable, [sys.executable, *sys.orig_argv[1:]])
