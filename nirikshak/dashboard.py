"""Launch the Streamlit dashboard: python -m nirikshak.dashboard [streamlit options]

Prefer this over `streamlit run app/dashboard.py` on Linux: importing nirikshak first
applies the libgomp workaround (see nirikshak/_runtime.py) before the server starts,
instead of restarting the server when the first browser session loads the script.
"""

import sys
from pathlib import Path

from streamlit.web.cli import main

APP = Path(__file__).resolve().parents[1] / "app" / "dashboard.py"

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", str(APP), *sys.argv[1:]]
    sys.exit(main())
