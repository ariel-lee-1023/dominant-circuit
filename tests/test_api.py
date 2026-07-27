"""Public API and no-blocking-I/O checks."""

import ast
from pathlib import Path

import pytest


def test_readme_api_imports():
    from dominant_circuit import dispatch, InputContract  # noqa: F401


def test_no_input_calls_in_src():
    """Static check: input( must not appear under src/."""
    src = Path(__file__).resolve().parents[1] / "src"
    offenders = []
    for py in src.rglob("*.py"):
        tree = ast.parse(py.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = getattr(func, "id", None) or getattr(func, "attr", None)
                if name == "input":
                    offenders.append(str(py))
    assert not offenders, f"blocking input() found in: {offenders}"
