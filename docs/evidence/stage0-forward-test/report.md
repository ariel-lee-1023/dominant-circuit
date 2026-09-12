# Independent Stage 0 synthetic forward test

Scope: one independent host enactment of the three supplied synthetic turns. This is not a live-host reliability study, a statistical result, or human release signoff. The implementation was read, not edited. No external records were collected, people contacted, or interventions performed.

## Artifacts

- `transcript.md`: exact supplied user turns, delivered host responses, six rendered fields, and update summaries.
- `turns.json`: readable structured turn summaries and rendered fields.
- `turn-1-state.json`, `turn-2-state.json`, `turn-3-state.json`: tagged serialized Investigation state after each delivered response.
- `trace.json`: six state snapshots including pending evidence and inaccessible-plan states.
- `run_forward_test.py`: reproducible host adapter for this single enactment.
- `example-smoke-output.txt`: successful run of the skill's supplied example.

Run with `PYTHONPATH=/private/tmp/dc-stage0-work/src /private/tmp/dc-env/bin/python /private/tmp/dc-stage0-forward-test/run_forward_test.py`.

## Outcomes

1. Initial account: training/coordination and demand/case mix are complementary possibilities. The reported hiring/slowdown sequence is not promoted to causal evidence. Ticket comparison remains conditional on unknown access, with a memory fallback.
2. Returned report: the colleagues' accounts are preserved as secondhand, unplanned evidence with unknown sampling and repair status. The inaccessible ticket plan is recorded as unavailable, then replaced by a feasible descriptive recollection step. The demand account expands to possible unresolved-issue recurrence. The manager's closure objective remains separately attributed and no agreement with the user's slowdown inquiry is inferred.
3. Counterexample and request for simplicity: the user's diagram-fit objection is stored and acknowledged, and the exact reopening episode is preserved as an Observation. Five reopening events are separated from the one reported underlying issue. The proposed account remains unassessed, since the cause of those events and their queue-wide importance are unknown. The next step is a two-minute private sequence from memory, with an explicit stop if details cannot be recalled.

Each delivered turn ends `closed_for_current_purpose` with a justified next observation, no pending reviews, and no solver handoff. This means the present turn is complete, not that the causal question is settled. Goals become contested after the manager's preference is reported and remain so. No collection authorization event was invented. State round trips preserved the rendered fields. Two observations and one correction were retained.

## Operational/API experience

The imported API and supplied example ran without exceptions. It was necessary to read the implementation for exact constructor signatures; the prose API documentation is useful but does not provide complete call signatures. Immutable-return discipline worked: each operation's result became the current state, and `reopen` was used after closing a prior turn. The unplanned colleague report was reviewed with `inconclusive`, rather than pretending it was the originally proposed ticket comparison. The reopening episode could be linked to the previous descriptive memory plan without claiming falsification.

The adapter did not run a solver, formal identification, or stability analysis; none was warranted. It used qualitative boundary comparison only. It did not revise the goal to the manager's preference. It also did not record a measurement correction: no earlier supplied operational definition had actually been corrected; the event/issue distinction is a proposed boundary clarification.

## Independent concerns

1. **Reference instructions conflict with the revised skill.** `stage0/references/reference-meadows-thinking-in-systems.md` still says to always run a mechanical dimensional check, emit `BoundaryFork`, and treat interventions followed by worsening as presumptive reinforcing-loop or delay evidence. It names `DimensionalMismatch`, `LoopDominanceUndetermined`, and a mechanical capability 5.2. These are not available in the Investigation API I read. The reference also insists on drawing the boundary and naming accumulations before policy, whereas SKILL.md explicitly makes dynamic vocabulary optional and warns against invented stocks, flows, and mandatory frameworks. A host following the linked reference literally could undo the revised conversational behavior. This test prioritized the explicit SKILL.md guidance and did not invent those structures or capabilities.
2. **The compact renderer can be too long for a simple next-step request.** Responses with the required six-field markdown were 349, 415, and 428 words. Turn 3 starts with a direct action, but then repeats boundaries, formal-limit boilerplate, and relationship status. The test is compliant with preserving the six fields, but does not demonstrate that this format is comfortable for a user explicitly asking to stop discussing a diagram.
3. **Renderer omissions require host supplementation.** `render_fields()` does not display `ObservationPlan.method`, `WorkingAccount.assessment_scope`, or the concrete details in `Observation.missingness`/`selection_limits`. The host prose supplies the action and evidence qualification here. A thin adapter that only forwards `to_markdown()` may preserve the six headings while losing the actionable procedure and the exact limits that justify its assessment.
4. **Access and disagreement are coarse fields.** `ParticipantPosition.can_access` is one Boolean, so this test had to explain that `False` refers specifically to ticket-level logs, while memory remains available. `contested_goals` also marks any differently worded or unresolved goals contested; it records uncertainty conservatively but does not itself establish an actual participant conflict. The transcript avoids inferring a direct disagreement or claiming what the manager is authorized to do.

These are observations from this enactment and source inspection, not a quantified reliability evaluation. I did not modify the implementation or attempt to resolve the concerns.
