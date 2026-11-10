"""Local entry: streamlit run app.py

The Fusion-hosted copy lives in modules/catalyst_context/streamlit/catalyst_context_app/.
"""

from __future__ import annotations

import sys
from pathlib import Path

APP = Path(__file__).resolve().parent / "modules" / "catalyst_context" / "streamlit" / "catalyst_context_app"
sys.path.insert(0, str(APP))

from main import run

run()
