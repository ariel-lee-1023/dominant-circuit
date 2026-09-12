# Synthetic independent forward test

This is one synthetic forward test, not a live-host reliability study or human release signoff. No records were collected, people contacted, or interventions performed.

## Turn 1

**User:** Our support queue got slower after hiring three people. Where should I look?

**Host:** Start by separating time spent handling work from work that keeps coming back. Hiring can coincide with more training and handoffs, but the timing alone does not tell us the cause. If ticket histories are already available to you, compare a few delayed cases using the same meaning of “slower.” If they are not, one episode you remember can still help.

## Starting model

Capacity and coordination: Training or coordination may temporarily consume experienced staff time. Includes ('support staffing', 'training', 'handoffs'); external ('new demand', 'unresolved product defects'); omitted/unknown ('definition of slower', 'case mix', 'repeat contacts'). A staffing-only account could miss changes in demand or count closures as resolutions. Assessment: unassessed. Demand and case mix: More requests, repeated requests, or harder cases may offset extra staff. Includes ('incoming support work', 'case complexity'); external ('product repair process',); omitted/unknown ('repeat-contact causes', 'volume change'). Contacts and underlying problems may not be the same unit. Assessment: unassessed.

## Observation instruction

closed_for_current_purpose: suggested exploratory observation: Compare delayed first-time requests with repeated issues around the hiring period. Source: Ticket histories only if already accessible within the user's role. Access: unknown; effort: A few already accessible episodes; owner: unknown. Retrospective reading should not change workflow; selection may favor memorable cases. This plan does not authorize external action.

## Commitments

user: Understand why support got slower (adopted)

## Prohibitions/limits

Model limits describe unanswered questions, not questions the user is forbidden to ask. No formal causal identification or stability result is established by completing this record. Meaning of the support slowdown: relevant, qualitative; The user describes changing work over time, so a limited systems boundary is useful

## Overturn conditions

Delays occur around training or handoffs: Capacity/coordination deserves closer observation; demand remains possible; The same underlying issue returns: Expand the boundary to recurrence causes; do not infer how prevalent it is; Both patterns appear: Keep complementary mechanisms; relative contributions remain unknown; No accessible comparable episodes or no clear pattern: Use one voluntarily recalled episode to clarify the unit; pause any inaccessible comparison

## Rival models

complementary: Capacity pressure and demand changes can coexist; neither is established by timing alone

**State update:** What changed: no reviewed revision yet. Next: Compare delayed first-time requests with repeated issues around the hiring period

## Turn 2

**User:** I asked two colleagues. They say people repeatedly contact us about bugs that never get fixed. I cannot access the ticket-level logs, and the manager wants us to focus only on closing more tickets.

**Host:** That gives us a concrete possibility: unresolved issues may be bringing work back into the queue. It does not show how much of the slowdown they explain. Ticket-level comparison is blocked by your access. The next useful step is a short account of one repeat-contact episode you already remember: what the person needed, what happened, and why they returned. Mark anything you do not know. Your manager’s closure target is recorded separately from your question about delay; we have not established agreement between those goals.

## Starting model

Capacity and coordination: Training or coordination may temporarily consume experienced staff time. Includes ('support staffing', 'training', 'handoffs'); external ('new demand', 'unresolved product defects'); omitted/unknown ('definition of slower', 'case mix', 'repeat contacts'). A staffing-only account could miss changes in demand or count closures as resolutions. Assessment: unassessed. Recurring unresolved issues: An unresolved issue may bring the same person back for further support work. Includes ('support contacts', 'underlying product issues', 'reported persistence of bugs'); external ('product repair ownership and priorities',); omitted/unknown ('actual repair status', 'recurrence prevalence', 'time consumed by returns'). Colleague reports may concentrate on frustrating cases; user-level recurrence and queue-wide rates remain distinct. Assessment: unassessed.

## Observation instruction

closed_for_current_purpose: suggested descriptive observation: Describe one already remembered repeat-contact episode and distinguish the contact from the underlying issue. Source: User's voluntary recollection, without consulting records or contacting anyone. Access: available; effort: One short recollection; owner: user if they choose to describe a memory. Recall may omit steps and favor unusual cases; no workflow change. This plan does not authorize external action.

## Commitments

user: Understand why support got slower (adopted); manager (as reported by user): Focus only on closing more tickets (unresolved)

## Prohibitions/limits

Model limits describe unanswered questions, not questions the user is forbidden to ask. No formal causal identification or stability result is established by completing this record. Goals remain contested; no consensus was inferred. Meaning of the support slowdown: relevant, stale; The user describes changing work over time, so a limited systems boundary is useful

## Overturn conditions

A person returns about the same underlying issue: Preserve the episode; separate contact/reopen events from distinct problems before interpreting closure totals; The return concerns a genuinely different issue: Do not count this episode as recurrence of one unresolved issue; The reason or sequence cannot be recalled: Keep the cause unresolved and pause until an accessible concrete episode is offered

## Rival models

complementary: Repeat work may coexist with training and handoff costs; the reports do not settle either contribution

**State update:** What changed: boundary_revision, mechanism_revision. Why: Include product issue persistence as a possible source of repeat work, retaining the limited secondhand evidence. Unresolved: The report makes unresolved-bug recurrence worth representing, but neither its prevalence nor its contribution to the slowdown is established; this was not the planned ticket comparison. Next: Describe one already remembered repeat-contact episode and distinguish the contact from the underlying issue

## Turn 3

**User:** I am not sure your diagram fits. Yesterday one person reopened the same issue five times. Can you just tell me what to do next?

**Host:** You do not need to make the diagram fit. Next, spend two minutes writing yesterday’s episode from memory: one underlying issue, five reported reopening events, and whatever you remember happening between them. Leave unknown reasons blank. This will help distinguish an unmet need from administrative reopening or another cause. If you cannot recall the sequence, stop there and keep the example as unresolved. No additional data collection is needed for this step.

## Starting model

Capacity and coordination: Training or coordination may temporarily consume experienced staff time. Includes ('support staffing', 'training', 'handoffs'); external ('new demand', 'unresolved product defects'); omitted/unknown ('definition of slower', 'case mix', 'repeat contacts'). A staffing-only account could miss changes in demand or count closures as resolutions. Assessment: unassessed. One issue, potentially repeated support work: A still-unmet need may produce repeated events; administrative reopening or another cause remains possible. Includes ('underlying issue', 'reopening events', 'support responses'); external ('product repair process',); omitted/unknown ('reopen reasons', 'identity or role of reopener', 'whether closure counted as resolution', 'representativeness'). One issue can generate several events, and an event does not establish a new issue or a confirmed unresolved defect. Assessment: unassessed.

## Observation instruction

closed_for_current_purpose: suggested descriptive observation: Write the remembered sequence for yesterday’s one issue, keeping unknown reopen reasons explicit. Source: User's voluntary recollection, without consulting records or contacting anyone. Access: available; effort: A two-minute private note from memory; owner: user if they choose to describe a memory. Memory can be incomplete; this is a suggestion for reflection, not an instruction to collect restricted records or change workflow. This plan does not authorize external action.

## Commitments

user: Understand why support got slower (adopted); manager (as reported by user): Focus only on closing more tickets (unresolved)

## Prohibitions/limits

Model limits describe unanswered questions, not questions the user is forbidden to ask. No formal causal identification or stability result is established by completing this record. Goals remain contested; no consensus was inferred. Meaning of the support slowdown: relevant, stale; The user describes changing work over time, so a limited systems boundary is useful

## Overturn conditions

The same need remained unmet across reopenings: Keep unresolved-need recurrence plausible for this episode; broader impact stays unknown; Reopens were administrative or the underlying need changed: Revise the episode explanation; do not infer persistent defects from reopen counts; Reasons cannot be recalled: Stop here and retain the episode; reopen the investigation if an accessible explanation becomes available

## Rival models

unresolved: Repeated events and capacity costs may coexist, but the single episode does not tell us why events occurred or how much work they created

**State update:** What changed: boundary_revision, unresolved_evidence. Why: Make event versus issue explicit in response to the user's mismatch, without silently changing historical metrics. Unresolved: The report makes unresolved-bug recurrence worth representing, but neither its prevalence nor its contribution to the slowdown is established; this was not the planned ticket comparison; I am not sure your diagram fits. Yesterday one person reopened the same issue five times.. Next: Write the remembered sequence for yesterday’s one issue, keeping unknown reopen reasons explicit