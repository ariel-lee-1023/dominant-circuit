# Stage 0 follow-up: implementation and release evidence

The implementation is committed as `9a6a96b86d608984ee323d1cbb6691f27cac3e98` on
`codex/engineering-stage0-followup`; release acceptance remains pending.
The reviewed worklist baseline is `b0fdf0a8644799b987ae0564febb85f75ea67f58`.
The actual target HEAD at reconciliation was `ac9e2ccec4290c37e19009a6aa2e1eb89a1cf537`,
with the original DC-00 through DC-13 remediation then uncommitted. That work passed
210 tests before this follow-up. Stage 0 had been removed from the current HEAD, so
this change restores its optional skill and source notes alongside a new shared-schema
investigation module. Both worklists are included in the implementation commit above. No package release
or deployment is claimed.

Implementation owner for S0-01 through S0-09: Codex (this task). Independent synthetic
forward tester: `stage0_forward_test` (Kant). This agent reviewed one bounded three-turn
scenario, not every acceptance criterion. A named human domain reviewer and engineering
release owner must still review and sign the evidence package; none has been invented.

| Item | Implementation and deterministic evidence | Remaining review |
|---|---|---|
| S0-01 | Shared provenance, versioned snapshots, plan/observation separation; `test_investigation.py` | Host event authenticity and faithful interpretation |
| S0-02 | Explicit boundaries, omissions, relationships; F01/F02/F05 | Relevance of proposed omissions |
| S0-03 | Feasibility, possible findings, inconclusive paths, attributed authorization; F04/F07/F10 | Practical effort and collection effects |
| S0-04 | Evidence review, goal/measurement revisions, transitive invalidation; F01/F03/F06/F09 | Evidence actually changes live-host framing |
| S0-05 | Optional methods, dependency records, no self-certified formal label; API tests/F08 | External method suitability when used |
| S0-06 | Raw corrections, participant positions and conflict retention; F05/F07/F11 | Clarity, attributed scope and question burden |
| S0-07 | Close/pause/reopen, bound handoffs and current report guards; API tests/F09 | Useful stopping and recovery in live interaction |
| S0-08 | All 11 fixtures, before/after state artifacts, paraphrases/order variants | Repeated live-host traces and human scoring |
| S0-09 | Skill, design, API/migration docs, examples, source drift guards | Human evidence-package signoff |

## Deterministic evidence

Before main integration, validation passed 256 tests with 91.04% coverage,
fatal-error lint, all three demos and skill-frontmatter validation.

Run `python -m pytest -q`. State invariants are in `tests/test_investigation.py`;
`tests/test_stage0_conversations.py` replays all 11 cases through explicit scripted
adapters, writes before/after state and final-field JSON to pytest's temporary directory,
and checks old handoff invalidation, unresolved observations and participant attribution.
The fixture definitions contain acceptable alternatives and reviewer rubrics decided
before evaluation. Paraphrase and evidence-order checks exercise adapter state behavior;
they do not demonstrate natural-language understanding or resistance to model anchoring.

Run `python examples/stage0_investigation.py` for a synthetic support-queue return cycle
and a direct offer comparison. Deterministic tests and the example perform no collection.

## Independent synthetic forward test

[Report](evidence/stage0-forward-test/report.md),
[transcript](evidence/stage0-forward-test/transcript.md) and
[state trace](evidence/stage0-forward-test/trace.json) retain the one independent run.
Artifacts retain the tester's content; the captured demo output's trailing blank
line was normalized for Git whitespace checks. The reproducible adapter records the
original local paths; use its source to rerun in an appropriate temporary location.
It is one synthetic enactment, not an F01-F11 repeated live evaluation. No human signoff
or estimated reliability follows from its successful transitions.

The reviewer found conflicting restored reference instructions and renderer omissions.
The final implementation rewrites those optional notes, removes unavailable capability
claims, and renders plan methods, assessment scopes and evidence limits. A late-evidence
regression also ensures findings under an older plan invalidate the current account's
handoff. The original review is retained rather than rewritten as if these fixes preceded it.

The reviewer measured 349, 415 and 428 words across the three delivered turns and flagged
repetition burden. The skill now permits concise clauses for each of the six fields.
That instruction has not been established as effective by a live user study. Participant
access and agreement fields remain conservative and coarse, with scope explained in prose.

## Release gates still pending

`scripts/check_release.py` reads `docs/release-evidence.json` and requires both the original
six cases and F01-F11. Stage 0 needs at least three uniquely identified live runs per case,
host model/version/prompt/tool configuration, triggering utterances, before/after states,
final output, named human scoring, revision and burden metrics, and zero observed critical
failures. Failures and reruns must remain in the evidence; one passing rerun cannot erase
a failure. Human review checks feasible next steps, faithful interpretation and whether
missing evidence, disagreement and stale recommendations were handled correctly.

Current live-host count is zero. Human review and engineering release signoff are pending.
The release check is expected to fail until those records exist. The original backlog's
P0 obligations and remaining gates are not waived by this follow-up.


## Integration with main for PR #8

Merged the main baseline `b0fdf0a8644799b987ae0564febb85f75ea67f58` into the
implementation branch. The combined tree passes 269 tests at 91.08% coverage,
fatal-error lint, all three demos and skill validation. Main's English-only output,
source attribution and discovery of unshaped investigations are retained.

The follow-up intentionally supersedes the earlier twelve-verdict taxonomy,
mandatory book order, four-field-only handoff and standing-volition prerequisite.
Its conceptual notes replace the old operational and unchecked formal-claim text;
the original source summaries remain accessible in Git history. Source-link checks,
the six rendered fields and evidence-provenance tests replace the old template
assertions. The support queue is an explicit public example, so it is no longer
represented as a blind acceptance probe; other held-out probe guards remain.

Repository integration does not supply the pending live-host evidence, human domain
review or package-release signoff. The release evidence gate still reports those gaps.
