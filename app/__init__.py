"""Compatibility package for running uvicorn from the repository root.

The real FastAPI package lives in backend/app. This extends the package search
path so commands like `uvicorn app.main:app --reload` work from the repo root.
"""

from pathlib import Path

_BACKEND_APP = Path(__file__).resolve().parent.parent / "backend" / "app"

if _BACKEND_APP.is_dir():
    __path__.append(str(_BACKEND_APP))  # type: ignore[name-defined]
else:
    raise ModuleNotFoundError("Could not find backend/app package.")
