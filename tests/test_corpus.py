"""Corpus/code drift guards.

This file exists because two prior failures went uncaught:

  * commit a2d99aa deleted 223 lines of c01 while claiming to fix a formula;
  * engines/sequential.py emitted `c03 §Bellman` and `c03 §belief`, citations
    that resolved to no numbered section, so no reader could check the claim.

Both are cheap to detect and expensive to discover later.
"""

from __future__ import annotations

import builtins
import keyword
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLUSTER_DIR = ROOT / "references" / "clusters"
SRC = ROOT / "src" / "dominant_circuit"

CLUSTERS = {"c01": "c01-optimal-stopping.md",
            "c02": "c02-multiple-objectives.md",
            "c03": "c03-sequential-decisions.md"}

# Floors set ~10% below the restored sizes. If a cluster legitimately shrinks,
# this must be updated in the SAME commit, with the reason in the commit body.
MIN_LINES = {"c01": 350, "c02": 600, "c03": 480}

# Structural anchors whose disappearance means content was truncated.
#
# The spec asks for four slots per cluster (scope/purpose, a compact worked
# algorithm or example, a decision table or validation constraints, and an
# invariants section). The three restored clusters do not use the same wording
# for these, and the clusters are authoritative and must not be edited
# (SPEC-2 working rule 3) -- so each entry names the heading that cluster
# actually uses to fill the slot.
REQUIRED_SECTIONS = {
    "c01": (
        "## Scope",                                     # scope
        "## Compact Worked Algorithm",                  # worked algorithm
        "## Decision Table",                            # decision table
        "## Key Invariants",                            # invariants
    ),
    "c02": (
        "## 1. Purpose and Scope",                      # scope
        "## 10. Compact Worked Elicitation Example",    # worked example
        "## 8. Validation Constraints",                 # validation constraints
        "## 11. Consistency Audit",                     # invariants / audit
    ),
    "c03": (
        "## 1. Probability and Bayes Update",           # scope-setting opener
        "## 11. Zero-Order End-to-End Decision Loop",   # worked algorithm
        "## 3. Markov Decision Process",                # constraint table
        "## 12. Validation Invariants",                 # invariants
    ),
}

# The tell that content was stripped and replaced with a pointer to something
# no longer present.
REMOVED_CONTENT_TELLS = ("original corpus", "see the original", "removed for brevity")

# A citation string literal emitted from src/.
CITATION_LITERAL_RE = re.compile(r'(?:citation|cite)\s*=\s*"([^"]*)"')
# A well-formed citation: cNN §X or cNN §X.Y
CITATION_RE = re.compile(r"^(c\d{2})\s*§\s*(\d+(?:\.\d+)?)$")
# A numbered markdown heading, e.g. "## 4. Discrete-n" or "### 4.1 Finite-n".
HEADING_NUM_RE = re.compile(r"^#{1,6}\s+(\d+(?:\.\d+)?)[.\s]")


# --- helpers (module level so other test modules can reuse them) -------------------

def cluster_path(key: str) -> Path:
    return CLUSTER_DIR / CLUSTERS[key]


def iter_source_files():
    return sorted(SRC.rglob("*.py"))


def extract_citations(path: Path) -> set[str]:
    """Every citation=/cite= string literal in one source file."""
    return set(CITATION_LITERAL_RE.findall(path.read_text(encoding="utf-8")))


def all_emitted_citations() -> dict[str, list[Path]]:
    """Maps each emitted citation string to the files that emit it."""
    found: dict[str, list[Path]] = {}
    for py in iter_source_files():
        for cite in extract_citations(py):
            found.setdefault(cite, []).append(py)
    return found


def heading_numbers(path: Path) -> set[str]:
    """Every section number that has a heading in this markdown file."""
    numbers = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = HEADING_NUM_RE.match(line)
        if m:
            numbers.add(m.group(1))
    return numbers


def section_body(path: Path, heading_prefix: str) -> str:
    """The text of one section, from its heading to the next heading of the
    same or shallower depth."""
    lines = path.read_text(encoding="utf-8").splitlines()
    depth = len(heading_prefix) - len(heading_prefix.lstrip("#"))
    out: list[str] = []
    collecting = False
    for line in lines:
        if line.startswith(heading_prefix):
            collecting = True
            continue
        if collecting and line.startswith("#"):
            this_depth = len(line) - len(line.lstrip("#"))
            if this_depth <= depth:
                break
        if collecting:
            out.append(line)
    return "\n".join(out)


# --- tests ------------------------------------------------------------------------

def test_all_clusters_exist():
    for key, name in CLUSTERS.items():
        assert cluster_path(key).is_file(), f"missing cluster {key}: {name}"


@pytest.mark.parametrize("key", sorted(CLUSTERS))
def test_cluster_minimum_sizes(key):
    """Guards against silent truncation. Floors set ~10% below the restored sizes:
       c01 >= 350 lines, c02 >= 600, c03 >= 480.
       If a cluster legitimately shrinks, this test must be updated in the SAME
       commit, with the reason in the commit body."""
    n = len(cluster_path(key).read_text(encoding="utf-8").splitlines())
    assert n >= MIN_LINES[key], (
        f"{CLUSTERS[key]} is {n} lines, below the {MIN_LINES[key]}-line floor. "
        "If this shrink is intentional, update MIN_LINES in this commit and say why."
    )


@pytest.mark.parametrize("key", sorted(CLUSTERS))
def test_required_sections_present(key):
    """Each cluster keeps its scope, worked algorithm/example, decision table or
    validation constraints, and invariants section."""
    text = cluster_path(key).read_text(encoding="utf-8")
    for heading in REQUIRED_SECTIONS[key]:
        assert heading in text, f"{CLUSTERS[key]} lost its '{heading}' section"


def test_every_emitted_citation_resolves():
    """Extract every citation=/cite= string literal from src/**/*.py.
       Parse 'cNN §X[.Y]'. Assert the cluster file exists AND contains a heading
       whose number matches X[.Y]. A citation like 'c03 §Bellman' must FAIL."""
    problems: list[str] = []
    headings_cache: dict[str, set[str]] = {}

    for cite, files in sorted(all_emitted_citations().items()):
        where = ", ".join(str(f.relative_to(ROOT)) for f in files)
        m = CITATION_RE.match(cite.strip())
        if not m:
            problems.append(f"{cite!r} ({where}) is not of the form 'cNN §X[.Y]'")
            continue
        cluster_key, number = m.group(1), m.group(2)
        if cluster_key not in CLUSTERS:
            problems.append(f"{cite!r} ({where}) names unknown cluster {cluster_key}")
            continue
        path = cluster_path(cluster_key)
        if not path.is_file():
            problems.append(f"{cite!r} ({where}) -> missing file {path.name}")
            continue
        if cluster_key not in headings_cache:
            headings_cache[cluster_key] = heading_numbers(path)
        if number not in headings_cache[cluster_key]:
            problems.append(
                f"{cite!r} ({where}) -> no §{number} heading in {path.name}"
            )

    assert not problems, "unresolvable citations:\n  " + "\n  ".join(problems)


def test_citation_checker_rejects_a_bad_citation(tmp_path):
    """The extractor must actually reject 'c03 §Bellman' — guards the guard."""
    fake = tmp_path / "engine.py"
    fake.write_text('x = 1\ncitation="c03 §Bellman"\n')
    assert extract_citations(fake) == {"c03 §Bellman"}
    assert CITATION_RE.match("c03 §Bellman") is None
    assert CITATION_RE.match("c03 §6") is not None


def test_no_dangling_internal_links():
    """Every relative markdown link in SKILL.md, README.md, AGENTS.md resolves
    to a file that exists."""
    link_re = re.compile(r"\]\(([^)]+)\)")
    dangling: list[str] = []
    for name in ("SKILL.md", "README.md", "AGENTS.md", "NOTICE.md"):
        doc = ROOT / name
        if not doc.is_file():
            continue
        for target in link_re.findall(doc.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path = (ROOT / target.split("#")[0]).resolve()
            if not path.exists():
                dangling.append(f"{name} -> {target}")
    assert not dangling, f"dangling relative links: {dangling}"


@pytest.mark.parametrize("key", sorted(CLUSTERS))
def test_no_pointers_to_removed_content(key):
    """No cluster may contain the phrases 'original corpus', 'see the original',
       or 'removed for brevity' — the tell that content was stripped and replaced
       with a pointer to something no longer present."""
    text = cluster_path(key).read_text(encoding="utf-8").lower()
    for tell in REMOVED_CONTENT_TELLS:
        assert tell not in text, (
            f"{CLUSTERS[key]} contains {tell!r} — content appears to have been "
            "replaced with a pointer to something no longer present."
        )


def test_parking_formula_matches_code():
    r"""c01 §10 must contain '\log p' and must NOT contain '\log(1-p)'.
        Locks T0 in place."""
    path = cluster_path("c01")
    body = section_body(path, "## 10.")
    assert body, "c01 §10 not found"
    assert r"\log p" in body, r"c01 §10 lost the corrected \log p form"
    assert "log(1-p)" not in body, r"c01 §10 still states the \log(1-p) form"
    # and nowhere else in the file either
    assert "log(1-p)" not in path.read_text(encoding="utf-8")


def test_parking_worked_values_match_the_code():
    """The Worked values table in c01 §10 must agree with parking_cutoff()."""
    from dominant_circuit.engines.stopping import parking_cutoff

    body = section_body(cluster_path("c01"), "## 10.")
    rows = re.findall(r"^\|\s*(0\.\d+)\s*\|\s*(\d+)\s*\|$", body, re.M)
    assert rows, "c01 §10 has no Worked values table"
    for p_str, d_str in rows:
        assert parking_cutoff(float(p_str)) == int(d_str), (
            f"c01 §10 says d*={d_str} for p={p_str}, code says "
            f"{parking_cutoff(float(p_str))}"
        )


def _skill_elicitation_fields() -> set[str]:
    """The contract fields named in SKILL.md's elicitation table."""
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    start = text.index("## Minimal Socratic elicitation loop")
    end = text.index("##", start + 10)
    section = text[start:end]
    return set(re.findall(r"\|\s*`([a-z_][a-z0-9_]*)`\s*\|", section))


def test_skill_question_bank_parity():
    """Every field in elicit.QUESTION_BANK appears somewhere in SKILL.md's
       elicitation section, and vice versa. Keeps T1.3 from rotting."""
    from dominant_circuit.core.elicit import QUESTION_BANK

    in_skill = _skill_elicitation_fields()
    in_bank = set(QUESTION_BANK)

    assert in_bank - in_skill == set(), (
        f"QUESTION_BANK fields missing from SKILL.md: {sorted(in_bank - in_skill)}"
    )
    assert in_skill - in_bank == set(), (
        f"SKILL.md names fields absent from QUESTION_BANK: {sorted(in_skill - in_bank)}"
    )


def test_skill_orchestration_symbols_exist():
    """Every function named in SKILL.md's orchestration block is importable from
    the package. Promoted from T1's done-when check.

    The spec's own snippet used `\\b(\\w+)\\s*\\(`, which also matches Python
    keywords (`import (`, `while (`) and attribute calls (`report.to_markdown()`)
    — the same category as the `get`/`rule` it already excluded. Keywords and
    attribute calls are excluded here instead of enumerating exceptions.
    """
    import dominant_circuit as d

    block = re.search(
        r"## Compact orchestration.*?```python(.*?)```",
        (ROOT / "SKILL.md").read_text(encoding="utf-8"),
        re.S,
    )
    assert block, "SKILL.md has no 'Compact orchestration' python block"

    names = set(re.findall(r"(?<![.\w])([a-z_][a-z0-9_]*)\s*\(", block.group(1)))
    names -= set(dir(builtins))
    names -= set(keyword.kwlist)

    missing = sorted(n for n in names if not hasattr(d, n))
    assert not missing, f"SKILL.md orchestration names non-existent API: {missing}"


def test_orchestration_block_imports_resolve():
    """The `from dominant_circuit import (...)` line in the block must work."""
    import dominant_circuit as d

    block = re.search(
        r"## Compact orchestration.*?```python(.*?)```",
        (ROOT / "SKILL.md").read_text(encoding="utf-8"),
        re.S,
    ).group(1)
    imported = re.search(r"from dominant_circuit import \((.*?)\)", block, re.S)
    assert imported, "orchestration block does not import from dominant_circuit"

    names = [n.strip() for n in imported.group(1).replace("\n", " ").split(",")]
    missing = [n for n in names if n and not hasattr(d, n)]
    assert not missing, f"orchestration block imports non-existent names: {missing}"


def test_every_cluster_declares_its_source():
    """Provenance line must survive; NOTICE.md depends on it."""
    for key in CLUSTERS:
        head = "\n".join(
            cluster_path(key).read_text(encoding="utf-8").splitlines()[:6]
        )
        assert "Source" in head, f"{CLUSTERS[key]} lost its Source attribution"


def test_worked_interaction_numbers_match_the_engine():
    """Every number in SKILL.md's worked interaction must be computed, not plausible.

    The transcript is the most-copied thing in the file; a stale number there is a
    fabricated citation with extra steps.
    """
    from dominant_circuit import (
        InputContract, Job, Horizon, Information, Payoff, dispatch,
    )

    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    start = text.index("## Worked interaction")
    section = text[start:text.index("\n## ", start + 10)]

    contract = InputContract(
        job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=50,
        information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
        recall_allowed=False, payoff_diverges=False,
    )
    report = dispatch(Job.STOPPING, contract)

    r_star = int(report.numeric["r_star"])
    assert f"r\\* = {r_star}" in section, f"transcript r* disagrees with engine ({r_star})"
    assert f"first {r_star - 1} of 50" in section
    assert f"From #{r_star} onward" in section
    assert f"P = {report.numeric['P_n']:.4f}" in section
    assert report.citation in section
    # the action string itself must be quoted faithfully. The transcript wraps it
    # across blockquote lines, so compare with markers and whitespace normalized.
    flat = re.sub(r"\s+", " ", section.replace("\n> ", " ").replace("**", ""))
    assert report.action.split(".")[0] in flat, (
        "SKILL.md's transcript no longer quotes report.action verbatim"
    )


def _python_blocks(doc: str) -> list[str]:
    return re.findall(r"```python\n(.*?)```", doc, re.S)


def test_readme_quick_start_actually_runs():
    """SPEC.md §15.10: README must describe only software that exists.

    The quick start is the first thing a user copies. Execute every python block
    in it rather than trusting that it still matches the API.
    """
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    blocks = _python_blocks(readme)
    assert blocks, "README has no python blocks to verify"
    for i, block in enumerate(blocks):
        # `...` placeholders stand in for host-side prompting
        exec(compile(block, f"README.md[block {i}]", "exec"), {})


def test_readme_teaches_the_current_independence_api():
    """The front door must not teach the deprecated IndependenceTest."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    quick_start = "\n".join(_python_blocks(readme))
    assert "IndependenceTest(" not in quick_start, (
        "README quick start uses the deprecated IndependenceTest; "
        "use IndependenceAssumption / record_independence (c02 §7.3)"
    )
    assert "record_independence" in quick_start


def test_readme_states_the_stage_ownership():
    """The design purpose — who owns which stage — must survive edits."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for stage in ("Elicitation", "Verification", "Computation", "Auditing", "Reporting"):
        assert stage in readme, f"README no longer names the {stage} stage"
    assert "Host" in readme and "Library" in readme


# Docs that must describe the code as it is right now.
LIVE_DOCS = ("README.md", "AGENTS.md", "SKILL.md", "DESIGN.md")

# Historical records of intent, deliberately NOT held to current reality: they
# describe target state at the time of writing and are partly superseded.
# SPEC.md §3, for instance, names test files that were later reorganised.
HISTORICAL_DOCS = ("SPEC.md", "docs/SPEC-2-PUNCHLIST.md")

# Things that look like a module path in prose, e.g. `engines/stopping.py`,
# `core/dispatch.py`, `src/dominant_circuit/core/audit.py`, `tests/test_corpus.py`.
MODULE_REF_RE = re.compile(
    r"`((?:src/dominant_circuit/|core/|engines/|tests/)[A-Za-z0-9_/]+\.py)"
    r"(?:::[A-Za-z0-9_]+)?`"
)


def test_live_docs_name_only_modules_that_exist():
    """The `solvers.py` class of bug: a document telling a reader to look at a file
    that is not there. Historical specs are exempt; docs describing current
    reality are not."""
    problems = []
    for name in LIVE_DOCS:
        doc = ROOT / name
        if not doc.is_file():
            problems.append(f"{name} is missing")
            continue
        for ref in set(MODULE_REF_RE.findall(doc.read_text(encoding="utf-8"))):
            path = ref if ref.startswith("src/") or ref.startswith("tests/") \
                else f"src/dominant_circuit/{ref}"
            if not (ROOT / path).is_file():
                problems.append(f"{name} references {ref!r} -> no such file")
    assert not problems, "docs name non-existent modules:\n  " + "\n  ".join(problems)


def test_no_live_doc_cites_solvers_py_as_real():
    """`solvers.py` was the pre-rewrite Stage 3 module, replaced by
    core/dispatch.py + engines/ (SPEC.md, defects D-12 and D-13).

    A live doc may *explain* its absence — that is how a reader of older text finds
    the current code — but none may present it as a file that exists. So any doc
    mentioning it must also say it does not exist.
    """
    disclaimers = ("does not exist", "must not be reintroduced",
                   "not missing", "superseded", "pre-rewrite")
    for name in LIVE_DOCS:
        text = (ROOT / name).read_text(encoding="utf-8")
        if "solvers.py" not in text:
            continue
        assert any(d in text for d in disclaimers), (
            f"{name} mentions solvers.py without saying it no longer exists"
        )
    # and the reconciliation must be findable from the design document
    assert "Naming note" in (ROOT / "DESIGN.md").read_text(encoding="utf-8")


def test_governing_documents_are_committed():
    """SPEC.md and docs/SPEC-2-PUNCHLIST.md are cited by AGENTS.md, DESIGN.md and
    the commit history. A fresh clone must be able to read them."""
    for name in HISTORICAL_DOCS + LIVE_DOCS:
        assert (ROOT / name).is_file(), f"{name} is cited but not committed"


def test_spec_layout_matches_the_package():
    """SPEC.md §3 defines the module layout; the package must still match it.

    This is what makes `engines/` canonical rather than `solvers.py`: SPEC.md
    records `solvers.py` as the *pre-rewrite* file (baseline commit a66504d) whose
    defects D-12 and D-13 were closed by replacing it with `core/dispatch.py`
    routing to the `engines/` package.
    """
    for module in ("core/contract.py", "core/elicit.py", "core/verify.py",
                   "core/audit.py", "core/dispatch.py", "core/report.py",
                   "core/errors.py", "engines/stopping.py",
                   "engines/multiobjective.py", "engines/sequential.py"):
        assert (SRC / module).is_file(), f"SPEC.md §3 requires {module}"
    assert not (SRC / "solvers.py").exists(), (
        "solvers.py is the superseded pre-rewrite module; it must not come back"
    )
