# Stage 0 investigation API and migration

This follow-up extends schema 2's `DecisionDescription` and `ConsequentialInput`. It adds
investigation workflow, working accounts, observation plans, returned observations,
review history and bound solver handoffs. It does not replace the solver, provenance,
readiness or preference APIs from [the original remediation](REMEDIATION.md).

## State and records

`Investigation.begin(id, description, event)` starts from a shared decision description.
Methods return a new investigation. Keep that returned object as the current persisted
state. `records` and `revisions` retain append-only snapshots; `latest_ref(kind, id)`
resolves the current revision and `get(ref)` returns a copy of its payload. References
have the form `account:capacity@2`, `goal:purpose@2`, `obs:episode@1` or `plan:tickets@1`.
Each record uses the existing consequential-input provenance, scope and revision fields.

Workflow is separate from model assessment. Drafted, ready-to-observe, awaiting-observation,
reviewing, paused and closed-for-current-purpose states do not establish truth. An account
starts unassessed. Evidence review can record support within a stated scope, weakening,
contradiction under stated assumptions or unresolved status. These are attributed host
interpretations, not results of a causal inference engine. State validation cannot prove
that an interpretation is faithful to the evidence; independent review remains necessary.

`propose_account` requires a boundary and a compact omission check. Record included,
external and unrepresented factors, visible observations, possible interventions, and an
outside observation or access limitation when consequential. `relate_accounts` records
competing, complementary, alternative-boundary or unresolved relationships. No rival quota
applies to simple comparisons. `WorkingAccount.working_use_event` records scoped use;
it does not establish empirical truth or authority to collect records.

## Plan, return, review, revise

`propose_observation` requires a useful question, source and method, possible findings
with implications, and an inconclusive outcome. Discriminating plans identify the exact
accounts and assumptions they address. Exploratory and descriptive plans remain useful.
Access and an explicit manageable-effort assessment determine whether a step is ready to observe;
effort assessment defaults to unknown. Collection ownership,
delay and effects can remain explicitly unknown. No information-value scores are invented.
`await_observation` additionally requires an attributed authorization event. The library
records supplied authorization; it neither authenticates it nor performs collection.

`receive_observation` accepts actual reports, measurements or external sources, with
context and source events. Missing values require an explanation of missingness. Proposed
results are not accepted as obtained observations. Preserve source episodes and selection
limitations even when the current account cannot interpret them. The raw record does not
become invalid merely because the plan that motivated collection later changes.

`review_observation` names the earlier possible finding and records its anticipated
implication, current interpretation and effects on accounts. Inconclusive or missing
observations cannot promote support or contradiction. Exploratory observations cannot be
labelled discriminating falsifications. Unplanned episodes receive unresolved review until
a useful interpretation or new plan is justified. Several revision classifications may
apply, but empirical review cannot silently revise the user's goal.

`revise_account` retains the earlier boundary/mechanism and links the revision to an
observation or correction. A revised account starts unassessed. `revise_goal` versions the
shared description without changing model assessment. `correct_observation` retains the
original report and invalidates dependent comparisons before revisiting causal claims.
`last_update()` summarizes what changed, why, what remains unresolved, and the next step.

## Correction, disagreement and stopping

`record_correction` accepts a counterexample, missing factor, disputed interpretation,
different goal or uncertainty in ordinary language, with attribution. Users need not edit
a graph or pass a conceptual quiz. Retain the correction and acknowledge it with a reason;
its original text and unresolved question remain in history. `record_position` preserves
participants' goals, agreement, role and access/authority when known. One participant's
adoption never establishes another's agreement, and different goals remain contested.

A useful next observation can end the current turn while the account remains provisional.
`close_cycle` records a justified next step, not completed causal understanding. `pause`
requires a reason and reopening trigger. `reopen` resumes from the latest valid records;
stale plans and handoffs do not become valid by changing the workflow state.

## Analytical dependencies and handoff

`AnalyticalResult` records target, method, applicability, reasons, assumptions, limits,
model specification and observable set when relevant. Qualitative and unresolved results
are supported. External formal claims require their certificate/model references and
remain `external_unverified`. No verifier for identification or formal dynamic stability
is implemented. Naming Meadows, Pearl or Page cannot produce `formally_checked` status.

The shared `dependency_closure` function is also used by the existing `DecisionSession`.
Revising a referenced input invalidates transitive dependants. Returned evidence immediately
invalidates affected analyses, handoffs and retained reports while review is pending. Raw
observations and unrelated analyses remain inspectable. Measurement-definition corrections
conservatively invalidate all analytical results and handoffs within the investigation;
this prevents old comparisons surviving a changed measurement context.

`handoff(name, contract, unresolved_conditions=(), analysis_refs=())` binds a copy of the
existing `InputContract` to the exact current goal, accounts and analytical dependencies.
It invokes the existing engine pipeline to check implemented prerequisites and records
completed checks. Solver readiness is separate from recommendation readiness. Pending
review, contested goals, stale dependencies or unresolved conditions prevent a usable
handoff. A direct static comparison needs no working causal account or observation plan.

Use `get_handoff` and `dispatch(job, contract, investigation=current_state)` together.
Dispatch rejects bound contracts when investigation context is missing, dependencies are
stale, review is pending, or the contract was changed after binding. Keep resulting reports
with `record_report` and retrieve them through `get_report`, which blocks stale readiness.
Detached historical objects cannot know about newer snapshots: the host must keep one
current persisted state per investigation and must not present old snapshot reports as
current recommendations. The library does not create an external action authorization.

## Rendering, serialization and older records

`render_fields()` returns the six fields: starting model, observation instruction,
commitments, prohibitions/limits, overturn conditions and rival models. `to_markdown()`
renders only that current compact view; full logs remain available separately. A model
limit describes a question the model cannot answer, not a prohibition on the user's inquiry.

The existing tagged `encode`/`decode` format includes investigation records and revisions.
Imported handoffs and reports require revalidation for current use. Scenario branches
retain evidence provenance and scope; old collection selection and handoff readiness do
not transfer. Use `migrate_stage0_snapshot` for older six-field outputs: their history is
unknown, assessment unassessed and observations empty. No historical observation or
adoption is invented.

## Examples and verification

Run `python examples/stage0_investigation.py` for a support queue whose initial capacity
account changes after returned evidence about unresolved defects, followed by a contrasting
static offer comparison. The example contains synthetic evidence and authorization events.
It performs no collection, contact, workflow change or intervention.

`tests/test_investigation.py` checks deterministic invariants. Conversation fixture tests
and release configuration are recorded in the Stage 0 release evidence. These scripted
adapter cases do not demonstrate that an arbitrary host model faithfully translates
language. Repeated live-host traces and human review remain distinct release gates.


## Host adapter limits

The renderer exposes the observation method, effort/delay, assessment scope and evidence
limits. The host can condense the six fields for short requests; it should not forward
long repeated logs. The independent synthetic test identified repetition burden, which
still needs live user-facing review. `ParticipantPosition` access and authority booleans
are conservative, coarse records: explain their resource scope in the position's role
and plan source. Differently worded or unresolved goals block an inferred consensus;
this syntactic safeguard does not prove that people actually disagree.

Historical record payloads survive serialization unchanged; imported handoffs/reports
are marked stale for current use at the investigation level. `get_report` applies the
current readiness view. Hosts should use these public methods rather than editing
nested record payloads. This is an append-only API convention and snapshot mechanism,
not tamper-proof storage or an evidence-authentication service.
