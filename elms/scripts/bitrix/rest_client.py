"""Load the canonical repository Bitrix transport inside a Frappe app image."""

from __future__ import annotations

import importlib.util
from pathlib import Path


_CANONICAL = Path(__file__).resolve().parents[3] / "scripts" / "bitrix" / "rest_client.py"
_SPEC = importlib.util.spec_from_file_location("elms_canonical_bitrix_rest_client", _CANONICAL)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - deployment invariant
    raise ImportError(f"Canonical Bitrix transport is unavailable: {_CANONICAL}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

for _name in dir(_MODULE):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_MODULE, _name)
