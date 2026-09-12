"""Non-interactive release evidence gate. Does not run or impersonate a live host."""

import json
from pathlib import Path
import sys


def check(evidence, cases):
    errors = []
    if not evidence.get("independent_review", {}).get("approved"):
        errors.append("Independent model and user-facing-claim review is pending")
    live = evidence.get("live_host", {})
    for field in ("model", "version", "prompt_sha256", "tool_configuration"):
        if not live.get(field):
            errors.append(f"Missing live-host configuration: {field}")
    runs = live.get("runs", [])
    for case in cases:
        observed = [r for r in runs if r.get("case_id") == case["id"]]
        if len(observed) < 3:
            errors.append(f"Insufficient live-host repetitions: {case['id']}")
        if case["id"].startswith("F"):
            ids = [r.get("run_id") for r in observed]
            if len(set(ids)) != len(ids) or any(not id for id in ids):
                errors.append(f"Missing or duplicate run identities: {case['id']}")
            if not evidence.get("independent_review", {}).get("reviewer"):
                errors.append("Stage 0 requires a named independent human reviewer")
        for run in observed:
            if case["id"].startswith("F"):
                required_metrics = (
                    "actual_revisions",
                    "unsupported_certainty",
                    "stale_outputs",
                    "unnecessary_reframings",
                )
                if (
                    run.get("kind") != "live_host"
                    or not run.get("reviewer")
                    or not isinstance(run.get("final_report"), dict)
                    or not {
                        "starting_model",
                        "observation_instruction",
                        "commitments",
                        "prohibitions_limits",
                        "overturn_conditions",
                        "rival_models",
                    }
                    <= run.get("final_report", {}).keys()
                    or not run.get("triggering_utterances")
                    or any(
                        type(run.get(k)) is not int or run[k] < 0
                        for k in required_metrics
                    )
                    or type(run.get("useful_next_step")) is not bool
                    or type(run.get("unresolved_retained")) is not bool
                ):
                    errors.append(
                        f"Missing Stage 0 trace, metrics or human review: {case['id']}"
                    )
                states = run.get("structured_states", [])
                if len(states) < len(case["turns"]) or any(
                    not isinstance(t, dict) or not {"before", "after"} <= t.keys()
                    for t in states
                ):
                    errors.append(f"Incomplete before/after turn states: {case['id']}")
                if run.get("unsupported_certainty", 0) or run.get("stale_outputs", 0):
                    errors.append(
                        f"Critical Stage 0 certainty or stale-output failure: {case['id']}"
                    )
            if (
                run.get("critical_failures") != []
                or not run.get("human_review")
                or not run.get("structured_states")
            ):
                errors.append(
                    f"Failed or incomplete live-host evaluation: {case['id']}"
                )
            if "unnecessary_questions" not in run or "useful_recovery" not in run:
                errors.append(f"Missing interaction-burden scoring: {case['id']}")
    return errors


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    evidence = json.loads(
        Path(
            sys.argv[1] if len(sys.argv) > 1 else root / "docs/release-evidence.json"
        ).read_text()
    )
    cases = json.loads((root / "tests/fixtures/host_release_cases.json").read_text())[
        "cases"
    ]
    cases += json.loads(
        (root / "tests/fixtures/stage0_conversations.json").read_text()
    )["cases"]
    errors = check(evidence, cases)
    print("\n".join(errors) if errors else "Release evidence gate passed")
    raise SystemExit(bool(errors))
