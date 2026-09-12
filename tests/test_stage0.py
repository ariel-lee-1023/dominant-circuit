"""Drift guards for the Stage 0 skill (`stage0/`).

Stage 0 now has deterministic state validation alongside its prose skill. Keep the
source and presentation drift checks that `tests/test_corpus.py` introduced:

  * the distillation that produced these files emitted unnumbered headings, so an
    earlier draft's `pearl §2.7`-style citations resolved to nothing -- the same
    defect as `c03 §Bellman`;
  * user-facing fields and epistemic promises must agree with the current API.

The follow-up replaces the twelve-verdict taxonomy and four-field handoff.
Legacy numbered citations remain checked if used; current Markdown links are
checked directly, without requiring unused section numbers.

Both are cheap to check here and expensive to discover from a wrong verdict later.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STAGE0 = ROOT / "stage0"
SKILL = STAGE0 / "SKILL.md"

REFS = {
    "meadows": STAGE0 / "references" / "reference-meadows-thinking-in-systems.md",
    "pearl": STAGE0 / "references" / "reference-pearl-book-of-why.md",
    "page": STAGE0 / "references" / "reference-page-model-thinker.md",
    "frankfurt": STAGE0 / "references" / "reference-frankfurt-freedom-of-the-will.md",
}

# `meadows §2.4`, `pearl §2.10`, `page §2.5`, `frankfurt §2.3` -- the anchor scheme SKILL.md
# used historically. Keep this registry to catch dangling numbered citations if
# reintroduced; the current skill selects methods by applicability, not book order.
CITATION_RE = re.compile(r"\b(meadows|pearl|page|frankfurt)\s+§(\d+(?:\.\d+)?)")

# Bare continuation anchors: `§2.9` inside a cell whose first citation named the book.
BARE_ANCHOR_RE = re.compile(r"§(\d+(?:\.\d+)?)")

# `## 2. Frameworks` / `### 2.4 System Boundary`
HEADING_RE = re.compile(r"^#{2,3}\s+(\d+(?:\.\d+)?)[.\s]", re.MULTILINE)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing Stage 0 file: {path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def anchors() -> dict[str, set[str]]:
    return {book: set(HEADING_RE.findall(_read(path))) for book, path in REFS.items()}


def test_stage0_files_exist():
    _read(SKILL)
    for path in REFS.values():
        _read(path)


def test_skill_declares_a_name():
    text = _read(SKILL)
    assert text.startswith("---\n"), "SKILL.md has no YAML frontmatter"
    front = text.split("---", 2)[1]
    assert re.search(r"^name:\s*\S+", front, re.MULTILINE), "frontmatter has no name"
    assert re.search(r"^description:\s*\S+", front, re.MULTILINE), "no description"


def test_reference_links_and_fragments_resolve():
    """Current notes use Markdown links; numbered citations are optional."""
    for path in (SKILL, *REFS.values()):
        headings = re.findall(r"^#{1,6} (.+)$", _read(path), re.MULTILINE)
        assert headings, f"{path.name} has no inspectable structure"
        for link in re.findall(r"\]\(([^)]+)\)", _read(path)):
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            location, _, fragment = link.partition("#")
            target = path.parent / location if location else path
            assert target.is_file(), f"Missing reference: {link} in {path.name}"
            if fragment:
                anchors = {
                    re.sub(r"[^\w -]", "", h.lower()).replace(" ", "-")
                    for h in re.findall(r"^#{1,6} (.+)$", _read(target), re.MULTILINE)
                }
                assert fragment in anchors, f"Missing section: {link} in {path.name}"


def test_every_stage0_citation_resolves(anchors):
    """`c03 §Bellman`, one layer up: a citation that points at no numbered section."""
    problems: list[str] = []
    for name, path in [("SKILL.md", SKILL), *[(p.name, p) for p in REFS.values()]]:
        for book, anchor in CITATION_RE.findall(_read(path)):
            if anchor not in anchors[book]:
                problems.append(f"stage0/{name}: {book} §{anchor} -> no such section")
    assert not problems, "unresolvable Stage 0 citations:\n  " + "\n  ".join(problems)


def test_self_citations_inside_a_reference_resolve(anchors):
    """A reference file citing its own `§2.4` must also hit a real heading."""
    problems: list[str] = []
    for book, path in REFS.items():
        text = _read(path)
        for anchor in set(BARE_ANCHOR_RE.findall(text)):
            named = {a for _, a in CITATION_RE.findall(text)}
            if anchor in named:
                continue  # cross-book citation, checked above
            if anchor not in anchors[book]:
                problems.append(f"{path.name}: own §{anchor} -> no such section")
    assert not problems, "unresolvable self-citations:\n  " + "\n  ".join(problems)


def test_completed_workflow_does_not_certify_an_account():
    """The new workflow replaces verdict counts without promoting causal truth."""
    import runpy

    example = runpy.run_path(str(ROOT / "examples/stage0_investigation.py"))
    state = example["support_queue"]()
    state = state.propose_observation(
        "tickets", example["ticket_plan"](state), "test:plan"
    )
    before = state.get(state.current_model_ref)
    closed = state.close_cycle(
        "A feasible next observation finishes the turn", "test:close"
    )
    assert closed.workflow == "closed_for_current_purpose"
    assert closed.get(closed.current_model_ref) == before
    assert before.assessment == "unassessed"


def test_output_contract_has_all_six_fields():
    """The six fields stay aligned with the renderer after the protocol revision."""
    import runpy

    body = _read(SKILL).split("## Preserve the six user-facing fields", 1)
    assert len(body) == 2
    labels = re.findall(r"^\d+\.\s+\*\*(.+?):\*\*", body[1], re.MULTILINE)
    expected = [
        "Starting model",
        "Observation instruction",
        "Commitments",
        "Prohibitions/limits",
        "Overturn conditions",
        "Rival models",
    ]
    assert labels == expected
    state = runpy.run_path(str(ROOT / "examples/stage0_investigation.py"))[
        "support_queue"
    ]()
    assert re.findall(r"^## (.+)$", state.to_markdown(), re.MULTILINE) == expected


def test_proposed_numeric_findings_cannot_become_observations():
    """Existing measurements may be numeric; hypothetical numbers are not evidence."""
    from dominant_circuit import ConsequentialInput, Observation

    proposal = ConsequentialInput(
        "predicted-reopens", 5, origin="model_proposal", evidence_ref="test:scenario"
    )
    with pytest.raises(ValueError):
        Observation(proposal, "Hypothetical outcome, not an obtained report")
    measured = ConsequentialInput(
        "reported-reopens",
        5,
        origin="user_report",
        evidence_ref="test:reported-episode",
    )
    assert Observation(measured, "User's actual episode").finding.value == 5


def test_no_dangling_links_in_stage0_skill():
    link_re = re.compile(r"\]\(([^)]+)\)")
    dangling = [
        target
        for target in link_re.findall(_read(SKILL))
        if not target.startswith(("http://", "https://", "#", "mailto:"))
        and not (STAGE0 / target.split("#")[0]).exists()
    ]
    assert not dangling, f"dangling links in stage0/SKILL.md: {dangling}"


def test_references_do_not_hardcode_acceptance_probe_answers():
    """An earlier draft wrote the wording of an acceptance question into the corpus,
    which turned a blind probe into a lookup. Keep the probes out of the refs."""
    leaked = [
        path.name
        for path in REFS.values()
        if re.search(r"acceptance[- ](question|probe)", _read(path), re.IGNORECASE)
    ]
    assert not leaked, f"acceptance-probe wording leaked into: {leaked}"


# Scenario fingerprints for the blind acceptance probes. Each entry is a set of terms
# whose CO-OCCURRENCE identifies that probe's scenario; a document containing all of
# them has, in effect, published the answer.
#
# These live here, and only here, on purpose. A test file is not loaded at inference
# time; the reference corpus and the host-facing skill are. Naming the scenarios in a
# document the model reads is the leak this guards against, so the registry has to sit
# outside every such document.
# The support-queue case is now explicitly a public worked example and fixture
# (S0-08/S0-09), so it cannot be represented as a blind acceptance probe.
PROBE_FINGERPRINTS = {
    "feature-retention": {"feature", "retention", "cohort"},
    "price-equilibrium": {"house", "prices", "stabilize"},
}

# Documents a host AI or a distilling model actually reads.
MODEL_FACING_DOCS = (
    *REFS.values(),
    SKILL,
    ROOT / "SKILL.md",
    ROOT / "README.md",
    ROOT / "DESIGN.md",
)


@pytest.mark.parametrize("probe", sorted(PROBE_FINGERPRINTS))
def test_no_model_facing_doc_reproduces_a_probe_scenario(probe):
    """The phrase-level guard above is weaker than its own docstring.

    The near-miss it did not catch: a worked transcript in the root SKILL.md that
    reproduced a probe's scenario and its whole expected answer without ever using
    the words "acceptance probe". A blind probe is worth nothing once a document the
    model reads contains the case, so match on scenario co-occurrence, and check the
    host-facing docs too rather than only the three references.
    """
    terms = PROBE_FINGERPRINTS[probe]
    leaked = []
    for path in MODEL_FACING_DOCS:
        if not path.is_file():
            continue
        words = set(re.findall(r"[a-z]+", path.read_text(encoding="utf-8").lower()))
        if terms <= words:
            leaked.append(str(path.relative_to(ROOT)))
    assert not leaked, (
        f"probe {probe!r} scenario ({sorted(terms)}) appears in: {leaked}. "
        "Pick a different worked example; that one is an acceptance probe."
    )


def test_root_router_can_discover_unshaped_investigations():
    text = (ROOT / "SKILL.md").read_text()
    front = text.split("---", 2)[1]
    assert "uncertain decision framing" in front and "Stage 0" in front
    assert "[Stage 0](stage0/SKILL.md)" in text
