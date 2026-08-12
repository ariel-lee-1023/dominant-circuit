"""Drift guards for the Stage 0 skill (`stage0/`).

Stage 0 is a prose skill, not code, so the usual test suite cannot reach it. But it
has exactly the failure modes `tests/test_corpus.py` was written for:

  * the distillation that produced these files emitted unnumbered headings, so an
    earlier draft's `pearl §2.7`-style citations resolved to nothing -- the same
    defect as `c03 §Bellman`;
  * the verdict table states its own counts in prose ("6 / 3 / 3"), which is the
    kind of number that silently stops matching the table under it.

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
}

# `meadows §2.4`, `pearl §2.10`, `page §2.5` -- the anchor scheme SKILL.md declares.
CITATION_RE = re.compile(r"\b(meadows|pearl|page)\s+§(\d+(?:\.\d+)?)")

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


def test_reference_headings_are_numbered(anchors):
    """The distillation pipeline dropped section numbers once. Numbered headings are
    the only thing that makes a `§X.Y` citation checkable by a reader."""
    for book, found in anchors.items():
        assert found, f"{book} reference file has no numbered headings at all"
        # Each file must at least number its framework block and its subsections.
        subsections = {a for a in found if "." in a}
        assert len(subsections) >= 5, (
            f"{book}: only {len(subsections)} numbered subsections -- "
            "framework blocks look unnumbered again"
        )


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


def test_verdict_counts_match_the_tables():
    """SKILL.md states the size of each verdict class in prose. Prose counts rot."""
    text = _read(SKILL)
    declared_total = re.search(r"(\w+) verdicts in three classes", text)
    assert declared_total, "SKILL.md no longer declares a verdict total"

    sections = {
        "7.1": re.search(r"### 7\.1 .*?\((\d+)\)", text),
        "7.2": re.search(r"### 7\.2 .*?\((\d+)\)", text),
        "7.3": re.search(r"### 7\.3 ", text),
    }
    assert sections["7.1"] and sections["7.2"], "verdict class headings lost their counts"

    # Bold verdict names are the row keys in the three tables.
    body = text.split("## 7. Verdict taxonomy", 1)[1].split("## 8.", 1)[0]
    rows = re.findall(r"^\|\s*\*\*(\w+)\*\*\s*\|", body, re.MULTILINE)
    assert len(rows) == len(set(rows)), f"a verdict is listed twice: {sorted(rows)}"

    words = {"Twelve": 12, "Eleven": 11, "Ten": 10, "Thirteen": 13}
    assert words.get(declared_total.group(1)) == len(rows), (
        f"SKILL.md declares '{declared_total.group(1)}' verdicts "
        f"but the tables list {len(rows)}"
    )

    n_true = int(sections["7.1"].group(1))
    n_forks = int(sections["7.2"].group(1))
    assert n_true + n_forks <= len(rows), "class counts exceed the total"


def test_output_contract_has_all_six_fields():
    """The six required fields are the deliverable. Losing one -- especially the
    observation instruction -- turns Stage 0 back into commentary."""
    body = _read(SKILL).split("## 6. Output contract", 1)
    assert len(body) == 2, "SKILL.md lost its output-contract section"
    contract = body[1].split("## 7.", 1)[0]
    fields = re.findall(r"^\d+\.\s+\*\*(.+?)\*\*", contract, re.MULTILINE)
    assert len(fields) == 6, f"output contract has {len(fields)} fields, expected 6: {fields}"
    assert any("bservation instruction" in f for f in fields), (
        "the observation instruction is the one field that may never be dropped"
    )


def test_stage0_emits_no_numbers_promise_is_stated():
    """Stage 0 hands off classifying fields only. If this promise disappears from
    the doc, the next contributor will helpfully fill in a numeric field."""
    text = _read(SKILL)
    assert "no numbers" in text.lower() or "never estimate" in text.lower()
    assert "assumption_provenance" in text, (
        "the mandatory assumption-provenance requirement is no longer stated"
    )


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
