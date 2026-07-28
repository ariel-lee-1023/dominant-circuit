"""Public API surface guard.

Commit a2d99aa was titled "Correct c01 §10 parking formula" and deleted 223
lines of corpus. Nothing caught it. tests/test_corpus.py puts size floors on
the clusters; this file extends the same protection to the public API, so that
removing an export is a deliberate, visible act rather than a side effect.
"""

from __future__ import annotations

import dominant_circuit

# The full __all__ as of completion of T8.
EXPECTED_EXPORTS = {
    # contract + enums
    "InputContract", "Job", "Horizon", "Information", "Payoff", "RiskAttitude",
    "AttributeRange", "IndependenceTest", "IndependenceAssumption",
    # output contract
    "OutputReport", "AuditResult", "InvariantResult", "SensitivityEntry",
    # zero-order expansion (零阶展开)
    "PerturbationTerm", "relative_shift",
    "ORDER_ZERO", "ORDER_FIRST", "ORDER_OVERTURN", "ORDER_HARD", "ORDER_DROPPED",
    # error taxonomy
    "DominantCircuitError", "ContractIncomplete", "PreconditionViolation",
    "NoOptimalStoppingRuleExists", "IndependenceNotVerified", "NonMarkovProcess",
    "UnclassifiedVariant", "AuditFailure", "NotInCorpus",
    # pipeline
    "dispatch", "missing_fields", "next_question", "require_complete",
    "classify_job", "QUESTION_BANK", "verify_preconditions",
    "run_validation_invariants", "check_range_fixed_weights", "INVARIANT_FIELDS",
    # engine A — optimal stopping (c01)
    "optimal_cutoff", "asymptotic_cutoff", "parking_cutoff", "parking_cutoff_exact",
    "threshold_percentile", "threshold_rule", "threshold_schedule",
    "cost_aware_threshold", "burglar_ceiling",
    "cutoff_unknown_horizon_uniform", "cutoff_stochastic_stop",
    "cutoff_with_recall", "cutoff_with_rejection",
    "Calibration", "CALIBRATIONS", "check_assumption_set_match",
    # engine B — multiple objectives (c02)
    "solve_multiplicative_k", "additive_value", "multiplicative_utility",
    "mutual_independence_holds", "uncovered_independence_subsets",
    "required_independence_subsets", "run_flip_test", "FlipTestResult",
    "efficient_frontier", "dominates", "dominance_screen",
    "check_independence_and_form",
    # stage 2 elicitation helpers — the flip-test checkpoint, host-drivable
    "independence_questions", "record_independence", "FLIP_TEST_QUESTION",
    # engine C — sequential decisions (c03)
    "belief_update", "value_iteration",
}


def test_public_api_surface_is_stable():
    """Removing a public export must be a deliberate, visible act. If this test
    fails because you intentionally removed a symbol, update EXPECTED_EXPORTS in
    the SAME commit and state the removal in the commit body."""
    actual = set(dominant_circuit.__all__)
    removed = EXPECTED_EXPORTS - actual
    assert not removed, (
        f"public exports disappeared: {sorted(removed)}. "
        "If intentional, update EXPECTED_EXPORTS in this commit and add a "
        "'REMOVES:' line to the commit body (see AGENTS.md, Change discipline)."
    )
    assert actual >= EXPECTED_EXPORTS


def test_every_export_actually_resolves():
    """__all__ must not name something the package does not provide."""
    missing = sorted(n for n in dominant_circuit.__all__
                     if not hasattr(dominant_circuit, n))
    assert not missing, f"__all__ names unimportable symbols: {missing}"


def test_no_duplicate_entries_in_all():
    names = list(dominant_circuit.__all__)
    dupes = sorted({n for n in names if names.count(n) > 1})
    assert not dupes, f"__all__ has duplicate entries: {dupes}"


def test_star_import_matches_all():
    ns: dict = {}
    exec("from dominant_circuit import *", ns)
    ns.pop("__builtins__", None)
    assert set(ns) == set(dominant_circuit.__all__)


def test_package_is_typed_and_versioned():
    from pathlib import Path

    assert dominant_circuit.__version__
    marker = Path(dominant_circuit.__file__).parent / "py.typed"
    assert marker.is_file(), "py.typed marker missing; the package claims to ship types"


def test_version_is_consistent_between_package_and_pyproject():
    """A release that changes the public API must say so in one place, not two."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    declared = re.search(r'^version = "([^"]+)"',
                         (root / "pyproject.toml").read_text(), re.M).group(1)
    assert dominant_circuit.__version__ == declared, (
        f"package says {dominant_circuit.__version__}, pyproject says {declared}"
    )
