"""Test harness customizations for constrained CI environments."""

from __future__ import annotations

import os

# Disable auto-loading of third-party pytest plugins that require system GUI libraries.
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
