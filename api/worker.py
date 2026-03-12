import sys
from pathlib import Path

# Add the worker package to sys.path so relative imports resolve correctly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "worker"))

from app.main import app  # noqa: E402
