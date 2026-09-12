---
name: dominant-circuit-stage0
description: Propose and revise a working account of a decision problem through feasible observations, returned evidence, and user correction. Use for uncertain framing or investigation before a dominant-circuit solver handoff. Clearly specified static comparisons can bypass investigation.
---

# Stage 0: a revisable investigation

Offer a useful starting account when the user has not supplied one. Explain it through
concrete episodes, a small boundary comparison or a proposed observation. Explicitness
makes an account easier to question; it does not make an incorrect account cheap or
self-correcting. Correction requires accessible evidence, a return cycle, retained
counterexamples and a willingness to change the boundary or mechanism.

Use the existing `DecisionDescription` and `ConsequentialInput` records with
`Investigation` in `dominant_circuit.core.investigation`. The library validates state and
dependencies without conducting conversation or collecting evidence. Keep the returned
investigation as the current state after each operation. Detailed history is available
for inspection; it is not a questionnaire the user must complete.

Read [the investigation API and limits](../docs/STAGE0.md) when implementing an adapter.
Run [the support-queue and simple-comparison example](../examples/stage0_investigation.py)
for an executable evidence-return cycle.

## Choose only the analyses the question needs

A static comparison with adequate facts and scoped preferences can go directly to the
appropriate solver. Do not invent stocks, flows, equilibrium labels or rival theories.
For an uncertain mechanism, propose a concrete boundary and record what it includes,
treats as external, and cannot represent. One compact omission statement may suffice.

These resources are available methods, not a mandatory Meadows → Pearl → Page sequence:

- [Meadows: systems and boundaries](references/reference-meadows-thinking-in-systems.md)
  can help describe stocks, flows, feedback and omissions when dynamics matter.
- [Pearl: causal questions](references/reference-pearl-book-of-why.md) can help clarify
  intervention targets, graphs and observables when an intervention effect is the question.
- [Page: models and dynamic behavior](references/reference-page-model-thinker.md) can
  help compare model classes and identify an appropriate dynamic analysis.
- [Frankfurt: reflective preferences](references/reference-frankfurt-freedom-of-the-will.md)
  is optional when the user wants to discuss standing commitments. It is not a prerequisite
  for a decision-specific preference or useful assistance.

Record applicability as relevant, inapplicable or unresolved, with a reason. Naming a
framework is not an analytical result. Identification needs a target, graph/model and
observable set; formal stability needs a specified dynamic model and a suitable method.
This library verifies neither. Qualitative discussion remains useful; external claims
are recorded as `external_unverified`, with their source and limitations.

## Make an observation plan feasible

Distinguish competing explanations, complementary mechanisms, alternative boundaries
and relationships still unresolved. Capacity limits and recurring product defects may
coexist. Do not force a winner among explanations without evidence of exclusivity.

Before calling an observation discriminating, name the accounts or assumptions it
addresses and meaningful possible findings with their implications. Always include an
inconclusive outcome and a useful next step. Exploratory and descriptive observations
are legitimate, but do not license a claim of falsification.

Record the available source, access, collection owner if known, effort/delay if known,
and effects collection might have on the activity. Prefer manageable, useful steps;
do not fabricate probabilities or information-value scores. Where consequential,
look outside the favored account's usual measurements. If that evidence is inaccessible,
say so and offer an available descriptive step or a reasoned pause.

A plan is a suggestion. `ready_to_observe` is readiness for an investigation step, not
readiness to execute a recommendation. Record an attributed authorization event before
marking collection as awaiting observation. The library does not grant authority to
contact people, inspect restricted records, change workflows or run interventions.

## Require evidence to return

A user asking what might happen has not reported a result. Keep possible findings in the
plan. Add an `Observation` only for an actual report, measurement or source event, with
context, missingness, selection limitations and the original episode reference when useful.
Preserve episodes that the current account cannot explain; users need not edit a graph.

On return, compare the finding with the earlier plan and anticipated implications.
Record what is supported within limits, weakened, unchanged or not assessed. Missing
observations are not negative findings. Absence of contradiction is not confirmation.
Inconclusive evidence may leave the account unresolved and still yield a useful next step.

Classify a change as an input, mechanism, boundary or goal revision, measurement
correction, or unresolved evidence. Several classifications can apply. Review a changed
measurement definition before retaining the earlier causal story. A changed goal does
not falsify a causal model, and empirical evidence does not silently change preferences.
Use explicit account and goal revisions, retaining their predecessors and trigger events.

Offer natural correction paths: a counterexample, omitted factor, disputed interpretation,
a different goal, or uncertainty. Preserve participant attribution and disagreement.
A manager's preferred account does not erase a frontline report. Unknown access, ownership
and authority remain unknown. Never infer consensus across participants or ask repeatedly
for blanket agreement when scoped adoption is already clear.

## Finish a useful turn, pause or hand off

Finish the turn once a justified, feasible next observation or bounded comparison is
identified. Do not keep reframing without new evidence or a consequential unresolved
distinction. After review, explain what changed, why, what remains unresolved, and next.
Pause when access is unavailable, effort is disproportionate or the user chooses to defer;
record the reason and a reopening trigger without claiming the matter is settled.

Use an investigation handoff for solver work that depends on the account. It carries the
exact goal/model revisions, provenance, prerequisite checks and return conditions. Use
`dispatch(..., investigation=current_state)` on its bound contract and retain reports via
`record_report`/`get_report`. Pending evidence and changed dependencies invalidate old
handoffs and recommendations. On reopening, use the latest persisted investigation and
revalidate; do not reuse a detached old snapshot as the current decision state.

## Preserve the six user-facing fields

Use `investigation.render_fields()` or `to_markdown()` as the current view. For a short
next-step request, lead with the concrete action and condense each field to a clause or
sentence, retaining consequential evidence and access limits. Do not repeat unchanged
boundaries or formal-analysis boilerplate at length. Full state stays inspectable behind
the six fields. None of these fields is proof that an account is true.

1. **Starting model:** the proposed account, boundary, mechanisms and scoped assessment;
   for a simple comparison, the already stated decision may suffice.
2. **Observation instruction:** the useful next observation, source and access limits,
   or an explicit pause or direct-comparison route. Do not render unavailable collection
   as an executable instruction.
3. **Commitments:** working assumptions, scoped adoption and attributed participant goals.
   Keep contested goals visible; no conceptual quiz or identity commitment is required.
4. **Prohibitions/limits:** questions the model cannot answer, unresolved measurements,
   unsupported formal claims and practical access limits. A model's inability to answer
   a question does not mean the user is forbidden to ask it; consider changing the boundary.
5. **Overturn conditions:** possible findings and their anticipated implications, including
   inconclusive outcomes and reasons to reopen.
6. **Rival models:** competing, complementary, alternative-boundary or unresolved accounts
   when useful. An additional account is not required merely to fill a quota.

Old six-field outputs are historical snapshots with unknown investigation history. Use
`migrate_stage0_snapshot`; never infer that their suggested observations were obtained.
