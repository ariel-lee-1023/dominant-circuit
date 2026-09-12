"""Current skill/API/source links and release gates must not drift apart."""

import json
from pathlib import Path
import re
import runpy
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_stage0_references_resolve_and_remain_optional_resources():
    skill = (ROOT / "stage0/SKILL.md").read_text()
    links = re.findall(r"\]\(([^)]+\.md)\)", skill)
    assert len(links) >= 5
    for link in links:
        assert (ROOT / "stage0" / link).is_file()
    notes = list((ROOT / "stage0/references").glob("*.md"))
    assert len(notes) == 4
    for path in notes:
        text = path.read_text()
        assert "Source:" in text and "## Concepts available for investigation" in text
        assert "## Current Stage 0 application" in text
        assert "(../SKILL.md)" in text
        assert not any(
            old in text
            for old in (
                "BoundaryFork",
                "LoopDominanceUndetermined",
                "DimensionalMismatch",
                "NoEquilibriumExists",
            )
        )
    assert "stage0/SKILL.md" in (ROOT / "SKILL.md").read_text()
    assert "Stage 0: a revisable investigation" in (ROOT / "DESIGN.md").read_text()


def test_six_fields_and_example_exercise_revision_and_static_bypass():
    example = runpy.run_path(str(ROOT / "examples/stage0_investigation.py"))[
        "run_example"
    ]()
    fields = example["revised"].render_fields()
    assert set(fields) == {
        "starting_model",
        "observation_instruction",
        "commitments",
        "prohibitions_limits",
        "overturn_conditions",
        "rival_models",
    }
    assert "Method:" in fields["observation_instruction"]
    assert "Scope:" in fields["starting_model"]
    assert "Convenience sample" in fields["prohibitions_limits"]
    assert example["revised"].current_model_ref != example["initial"].current_model_ref
    assert not example["simple"].accounts


def release_fixture():
    cases = json.loads((ROOT / "tests/fixtures/stage0_conversations.json").read_text())[
        "cases"
    ]
    # Validator-only artificial input. This is never written to release evidence.
    evidence = dict(
        independent_review=dict(approved=True, reviewer="synthetic validator fixture"),
        live_host=dict(
            model="validator-fixture",
            version="test",
            prompt_sha256="test",
            tool_configuration="none",
            runs=[
                dict(
                    case_id=c["id"],
                    run_id=f"{c['id']}-{n}",
                    kind="live_host",
                    reviewer="synthetic fixture",
                    human_review=True,
                    triggering_utterances=[t["utterance"] for t in c["turns"]],
                    structured_states=[
                        dict(before=None, after={"test": True}) for _ in c["turns"]
                    ],
                    final_report={
                        k: "validator fixture"
                        for k in (
                            "starting_model",
                            "observation_instruction",
                            "commitments",
                            "prohibitions_limits",
                            "overturn_conditions",
                            "rival_models",
                        )
                    },
                    critical_failures=[],
                    unnecessary_questions=0,
                    useful_recovery=True,
                    actual_revisions=0,
                    unsupported_certainty=0,
                    stale_outputs=0,
                    unnecessary_reframings=0,
                    useful_next_step=True,
                    unresolved_retained=True,
                )
                for c in cases
                for n in range(3)
            ],
        ),
    )
    return cases, evidence


@pytest.mark.parametrize(
    "failure",
    [
        "critical",
        "duplicate",
        "synthetic",
        "missing_review",
        "missing_states",
        "certainty",
        "stale",
    ],
)
def test_stage0_release_gate_rejects_incomplete_or_failed_evidence(failure):
    cases, evidence = release_fixture()
    check = runpy.run_path(str(ROOT / "scripts/check_release.py"))["check"]
    assert check(evidence, cases) == []
    run = evidence["live_host"]["runs"][0]
    if failure == "critical":
        run["critical_failures"] = ["Unsupported claim"]
    elif failure == "duplicate":
        run["run_id"] = evidence["live_host"]["runs"][1]["run_id"]
    elif failure == "synthetic":
        run["kind"] = "deterministic_adapter"
    elif failure == "missing_review":
        run["reviewer"] = None
    elif failure == "missing_states":
        run["structured_states"] = [{}]
    elif failure == "certainty":
        run["unsupported_certainty"] = 1
    else:
        run["stale_outputs"] = 1
    assert check(evidence, cases)
