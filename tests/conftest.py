"""Shared test helpers for surface module tests."""

import os
import sys
import types
from unittest.mock import MagicMock, patch

# Ensure module scripts are importable
SURFACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def import_script(module_name, script_name):
    """Import a module script as a Python module, with datalib on path."""
    script_path = os.path.join(
        SURFACE_ROOT, "modules", module_name, "scripts", f"{script_name}.py"
    )
    # Ensure datalib is importable
    datalib_path = os.path.join(SURFACE_ROOT, "modules", "data", "scripts")
    if datalib_path not in sys.path:
        sys.path.insert(0, datalib_path)

    import importlib.util

    spec = importlib.util.spec_from_file_location(script_name, script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_test_data(tmp_path, domain, content):
    """Create a temporary data/ directory with TOML content for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    toml_file = data_dir / f"{domain}.toml"
    toml_file.write_text(content)
    return str(tmp_path)
