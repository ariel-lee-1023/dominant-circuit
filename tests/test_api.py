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


# --- T8.4 classify_job ------------------------------------------------------------

def test_classify_job_from_fields_only():
    from dominant_circuit import (
        classify_job, InputContract, Job, Horizon, AttributeRange, ContractIncomplete,
    )

    # explicit job wins
    assert classify_job(InputContract(job=Job.STOPPING)) is Job.STOPPING

    # stopping structure
    assert classify_job(InputContract(horizon=Horizon.FIXED_KNOWN, n=10)) is Job.STOPPING
    # multiobjective structure
    assert classify_job(
        InputContract(attributes=[AttributeRange("a", 0, 1)])
    ) is Job.MULTIOBJECTIVE
    # sequential structure
    assert classify_job(InputContract(states=["s"], actions=["a"])) is Job.SEQUENTIAL

    # nothing elicited -> ask, do not guess
    with pytest.raises(ContractIncomplete) as ei:
        classify_job(InputContract())
    assert ei.value.field == "job"

    # ambiguous structure -> ask, do not guess
    with pytest.raises(ContractIncomplete) as ei:
        classify_job(InputContract(n=10, attributes=[AttributeRange("a", 0, 1)]))
    assert ei.value.field == "job"


def test_classify_job_never_reads_prose():
    """D-06: classification must not depend on user text anywhere in the source."""
    import inspect
    from dominant_circuit.core import elicit

    src = inspect.getsource(elicit.classify_job)
    for tell in ("in text", "in prose", ".lower()", "query", "user_text", "message"):
        assert tell not in src, f"classify_job appears to inspect prose: {tell!r}"
