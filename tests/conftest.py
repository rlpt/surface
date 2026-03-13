"""Shared test helpers for surface module tests."""

import os
import sys
import types
from unittest.mock import MagicMock, patch

# Ensure module scripts are importable
SURFACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def import_script(module_name, script_name):
    """Import a module script as a Python module, with subprocess mocked."""
    script_path = os.path.join(
        SURFACE_ROOT, "modules", module_name, "scripts", f"{script_name}.py"
    )
    import importlib.util

    spec = importlib.util.spec_from_file_location(script_name, script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_dolt_db_dir(tmp_path):
    """Create a fake .dolt directory so check_db() passes."""
    db_dir = tmp_path / ".surface-db" / ".dolt"
    db_dir.mkdir(parents=True)
    return str(tmp_path / ".surface-db")


def mock_subprocess_csv(header, rows):
    """Create a mock CompletedProcess for dsql_csv/dsql_rows calls."""
    lines = [header] + rows
    stdout = "\n".join(lines) + "\n"
    return MagicMock(returncode=0, stdout=stdout, stderr="")


def mock_subprocess_empty():
    """Mock an empty result set (header only or nothing)."""
    return MagicMock(returncode=0, stdout="col\n", stderr="")


def mock_subprocess_val(value):
    """Mock a single-value result."""
    return MagicMock(returncode=0, stdout=f"col\n{value}\n", stderr="")
