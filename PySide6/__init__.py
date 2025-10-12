"""Compatibility shim that falls back to a lightweight PySide6 stub when real bindings are unavailable."""
from __future__ import annotations

import importlib.machinery
import os
import sys
from pathlib import Path

__all__ = ["QtCore", "QtGui", "QtWidgets", "QtTest"]

_FORCE_STUB_VALUES = {"1", "true", "yes", "on"}
_force_stub = os.getenv("PYSIDE6_FORCE_STUB", "").strip().lower() in _FORCE_STUB_VALUES
_module = sys.modules[__name__]
_project_root = Path(__file__).resolve().parent.parent
_real_loaded = False

if not _force_stub:
    for entry in list(sys.path):
        if not entry:
            continue
        try:
            entry_path = Path(entry).resolve()
        except Exception:  # pragma: nocover - defensive
            continue
        if entry_path == _project_root:
            continue
        spec = importlib.machinery.PathFinder.find_spec(__name__, [str(entry_path)])
        if spec and spec.loader and hasattr(spec.loader, "exec_module"):
            _module.__loader__ = spec.loader
            _module.__spec__ = spec
            if getattr(spec, "origin", None):
                _module.__file__ = spec.origin
            if spec.submodule_search_locations is not None:
                _module.__path__ = list(spec.submodule_search_locations)
            spec.loader.exec_module(_module)
            _module.__dict__.setdefault("__FAKE_PYSIDE6__", False)
            _real_loaded = True
            break

if _real_loaded and not _module.__dict__.get("__FAKE_PYSIDE6__", False):
    __FAKE_PYSIDE6__ = False
    __all__ = getattr(_module, "__all__", __all__)
else:
    __FAKE_PYSIDE6__ = True
    __version__ = "6.0.0"
    from . import QtCore, QtGui, QtWidgets, QtTest  # type: ignore[F401] re-export stubs
