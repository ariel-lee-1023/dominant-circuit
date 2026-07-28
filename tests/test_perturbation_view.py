"""The zero-order expansion (零阶展开) reported by every engine.

The load-bearing claim is that `first` (一阶修正) and `overturn` (翻盘) are
distinguished **structurally** — by whether the term stays inside the same
calibrated model — and never by how large the number moves. A 6% shift that stays
in one model is a correction; a 33% shift that changes models is an overturn.
Anything that reverses that is a bug, because it would let a big correction
masquerade as a new trunk (or worse, the reverse).
"""

import pytest

from dominant_circuit import (
    AttributeRange, Horizon, Information, InputContract, Job, Payoff,
    asymptotic_cutoff, dispatch, optimal_cutoff, record_independence,
)
from dominant_circuit.core.report import (
    ORDER_DROPPED, ORDER_FIRST, ORDER_HARD, ORDER_OVERTURN, ORDER_ZERO,
    PerturbationTerm, relative_shift,
)

VALID_ORDERS = {ORDER_ZERO, ORDER_FIRST, ORDER_OVERTURN, ORDER_HARD, ORDER_DROPPED}


def _stopping(n=50, **kw):
    base = dict(job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=n,
                information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
                payoff_diverges=False)
    base.update(kw)
    return dispatch(Job.STOPPING, InputContract(**base))


def _multiobjective(k_a=0.4, k_b=0.6):
    return dispatch(Job.MULTIOBJECTIVE, InputContract(
        job=Job.MULTIOBJECTIVE,
        attributes=[AttributeRange("a", 0, 10), AttributeRange("b", 0, 10)],
        scaling_constants={"a": k_a, "b": k_b},
        independence_assumptions=[
            record_independence({"a"}, {"b"}, "preferential", True),
            record_independence({"b"}, {"a"}, "preferential", True),
        ],
        alternatives=[{"name": "A", "a": 8, "b": 3},
                      {"name": "B", "a": 3, "b": 8},
                      {"name": "C", "a": 1, "b": 1}],
    ))


def _sequential(gamma=0.9):
    return dispatch(Job.SEQUENTIAL, InputContract(
        job=Job.SEQUENTIAL, horizon=Horizon.INFINITE_DISCOUNTED, gamma=gamma,
        markov_verified=True, states=["s0", "s1"], actions=["stay", "go"],
        # "go" pays 0 now but reaches the state that pays forever: the myopic
        # choice and the Bellman choice differ, which is the point of the test.
        reward={("s0", "stay"): 0.5, ("s0", "go"): 0.0,
                ("s1", "stay"): 2.0, ("s1", "go"): 0.0},
        transition={("s0", "stay"): {"s0": 1.0}, ("s0", "go"): {"s1": 1.0},
                    ("s1", "stay"): {"s1": 1.0}, ("s1", "go"): {"s1": 1.0}},
    ))


# --- structure ---------------------------------------------------------------------

@pytest.mark.parametrize("report_fn", [_stopping, _multiobjective, _sequential])
def test_every_engine_emits_an_expansion(report_fn):
    report = report_fn()
    assert report.perturbation, "engine emits no zero-order expansion"
    assert report.zero_order is not None, "expansion has no trunk"
    for term in report.perturbation:
        assert term.order in VALID_ORDERS, term.order
        assert term.label and term.citation
        assert term.citation.startswith(("c01 §", "c02 §", "c03 §"))


@pytest.mark.parametrize("report_fn", [_stopping, _multiobjective, _sequential])
def test_expansion_has_exactly_one_trunk(report_fn):
    """An expansion with two trunks is not an expansion. Every other term must be
    positioned relative to the single zero-order model."""
    report = report_fn()
    trunks = [t for t in report.perturbation if t.order == ORDER_ZERO]
    assert len(trunks) == 1, f"expected one trunk, got {[t.label for t in trunks]}"
    assert report.zero_order is trunks[0]
    # and the four buckets partition the rest exactly
    rest = (report.corrections + report.overturns
            + report.hard_constraints + report.dropped)
    assert len(rest) + 1 == len(report.perturbation)


# --- the load-bearing claim --------------------------------------------------------

def test_order_is_structural_not_magnitude():
    """The classical row: a +6% term is a CORRECTION and a -33% term is an
    OVERTURN. Sorting by magnitude would invert both."""
    report = _stopping(n=50)

    trunk = report.zero_order
    assert trunk.value == asymptotic_cutoff(50)[0] == 18
    assert "c01 §5" == trunk.citation

    (correction,) = report.corrections
    assert correction.value == optimal_cutoff(50)[0] == 19
    assert correction.citation == "c01 §4.1"
    assert abs(correction.relative_shift) < 0.10          # small...

    overturns = {t.value: t for t in report.overturns}
    assert set(overturns) == {30, 12}                     # 0.61n and 0.25n
    assert abs(overturns[12].relative_shift) > abs(correction.relative_shift)

    # ...and yet the SMALL-shift term is the correction while the LARGER-shift
    # term is an overturn. Order does not track magnitude.
    assert correction.order == ORDER_FIRST
    assert overturns[12].order == ORDER_OVERTURN


def test_relative_shift_is_signed():
    report = _stopping(n=50)
    by_value = {t.value: t for t in report.overturns}
    assert by_value[30].relative_shift > 0     # 0.61n is above the trunk
    assert by_value[12].relative_shift < 0     # 0.25n is below it
    assert relative_shift(12, 18) == pytest.approx(-1 / 3)
    assert relative_shift(5, 0) is None
    assert relative_shift("x", 1) is None


def test_hard_constraint_is_never_a_correction():
    """硬约束 must not be reported as a small quantity, in any engine."""
    for report in (_stopping(), _multiobjective(), _sequential()):
        for term in report.hard_constraints:
            assert term.order == ORDER_HARD
            assert term.relative_shift is None, (
                "a hard constraint must not carry a magnitude — it is a veto, "
                "not a term that scales"
            )


# --- per-engine trunks are the real corpus quantities -----------------------------

def test_stopping_trunk_flips_with_the_calibration_row():
    """Each Decision Table row is its own trunk; the classical figure becomes the
    overturn relative to it."""
    recall = _stopping(recall_allowed=True, recall_accept_prob=0.5)
    assert recall.zero_order.value == 30 and recall.zero_order.citation == "c01 §7"
    assert [t.value for t in recall.overturns] == [18]

    rejection = _stopping(rejection_prob=0.5)
    assert rejection.zero_order.value == 12 and rejection.zero_order.citation == "c01 §7"
    assert [t.value for t in rejection.overturns] == [18]

    # and neither reports a first-order refinement, because the corpus gives no
    # exact finite-n form for those rows
    assert recall.corrections == [] and rejection.corrections == []


def test_multiobjective_trunk_is_the_additive_k0_term():
    """c02 §5.3: additive is the k=0 special case, so it is the genuine trunk and
    the multiplicative interaction is the correction."""
    additive = _multiobjective(0.4, 0.6)          # sum = 1.0 -> k = 0 exactly
    assert additive.decision["form"] == "additive"
    assert additive.zero_order.citation == "c02 §5.3"
    assert additive.corrections == [], "k=0 needs no correction; it IS the trunk"

    multiplicative = _multiobjective(0.7, 0.6)    # sum = 1.3 -> k != 0
    assert multiplicative.decision["form"] == "multiplicative"
    (correction,) = [t for t in multiplicative.corrections if "multiplicative" in t.label]
    assert correction.order == ORDER_FIRST
    assert correction.relative_shift is not None


def test_multiobjective_records_the_dominance_screen_as_a_dropped_term():
    """主导平衡: alternatives with no causal control are thrown away, which is its
    own act — neither the trunk nor a refinement of it."""
    report = _multiobjective()
    screened = report.dropped
    assert screened, "dominance screening is not reported in the expansion"
    assert screened[0].order == ORDER_DROPPED
    assert "dominance screen" in screened[0].label
    assert "C" in screened[0].value          # dominated by both A and B


def test_sequential_trunk_is_the_myopic_action():
    """The Bellman equation is a series in gamma; gamma=0 keeps only R(s,a)."""
    report = _sequential(gamma=0.9)
    assert report.zero_order.value == "stay"          # myopic: 0.5 now beats 0.0
    assert report.zero_order.citation == "c03 §6"

    bellman = [t for t in report.corrections if "full Bellman" in t.label]
    assert bellman and bellman[0].value == "go"       # patience wins once discounted
    assert "myopic trunk is wrong here" in bellman[0].note


def test_sequential_reports_convergence_as_a_bounded_series():
    report = _sequential()
    conv = [t for t in report.corrections if "convergence" in t.label]
    assert conv and "gamma" in conv[0].note.replace("<=", "").lower()


# --- rendering ---------------------------------------------------------------------

def test_markdown_renders_the_expansion_with_the_chinese_headings():
    md = _stopping(n=50).to_markdown()
    assert "## Zero-order expansion (零阶展开)" in md
    assert "零阶 · trunk" in md
    assert "一阶修正" in md
    assert "翻盘" in md
    assert "硬约束" in md
    # trunk before Execute, so a reader meets the expansion before the verdict
    assert md.index("零阶展开") < md.index("## Execute")


def test_to_dict_carries_the_expansion():
    d = _stopping().to_dict()
    assert d["perturbation"], "expansion missing from to_dict"
    orders = {t["order"] for t in d["perturbation"]}
    assert orders <= VALID_ORDERS


def test_term_gloss_is_bilingual():
    t = PerturbationTerm(order=ORDER_FIRST, label="x", value=1, citation="c01 §5")
    assert "一阶修正" in t.gloss and "overturn" in t.gloss


# --- documentation may not drift from the engine -----------------------------------

def test_design_md_expansion_table_matches_the_engine():
    """DESIGN.md prints a worked expansion for n=50. Every figure in it must be
    computed, not plausible — the same rule the SKILL.md transcript is held to."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    text = (root / "DESIGN.md").read_text(encoding="utf-8")
    start = text.index("## The zero-order expansion")
    section = text[start:text.index("\n## ", start + 10)]
    # DESIGN.md uses a typographic minus (U+2212) in prose; Python formats ASCII.
    section = section.replace("\u2212", "-")

    report = _stopping(n=50)
    trunk = report.zero_order
    (correction,) = report.corrections
    overturns = {t.value: t for t in report.overturns}

    # the table's Value column
    assert f"| {trunk.value} | — |" in section
    assert f"| {correction.value} | {correction.relative_shift:+.0%} |" in section
    for value, term in overturns.items():
        assert f"| {value} | {term.relative_shift:+.0%} |" in section, value

    # and the prose claim about which is which
    assert f"The {correction.relative_shift:+.0%} term is a correction" in section
