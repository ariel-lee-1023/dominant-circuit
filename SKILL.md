---
name: dominant-circuit
description: "Master decision-mechanics router for choosing when to stop a search, how to trade off multiple objectives under certainty or uncertainty, and how to select or time actions in sequential/uncertain environments. Use when the user asks when to stop looking or searching, how to decide among finitely many alternatives with competing objectives, how to weigh tradeoffs or set scaling constants/utility weights, how to update beliefs with new evidence (Bayes/POMDP), how to pick an action under a Markov Decision Process or Bellman framework, or invokes phrases like optimal stopping, secretary problem, 37% rule, satisficing threshold, multiattribute utility, preferential/utility independence, expected utility, risk aversion, MDP, POMDP, belief update, value iteration, Q-learning, or Monte Carlo tree search. Also use for an uncertain decision framing or an unexplained change that needs a feasible observation and revisable working account through Stage 0. Not for unrelated brainstorming or simple factual lookups."
---

# Dominant-Circuit

Master router over three zero-order decision-mechanics clusters. This file dispatches, it does not restate the math. Open the linked cluster file before computing.

## When to use

Use when a request needs a **decision structure or investigation**, not just a factual lookup:
- A search/queue of options must be stopped at some point ("when do I stop looking/interviewing/dating/selling/renting").
- Multiple competing objectives/attributes must be traded off into one ranking or score ("which alternative is best given cost, quality, risk...").
- An action must be chosen now that affects a future state under known/unknown dynamics, or beliefs must be updated from observations ("what should I do next," "update my belief," "plan a sequence of moves").

If the situation has no clear alternatives or model yet, use Stage 0 to propose a provisional account and useful observation. A single-criterion factual lookup does not need the solver.

## When the framing needs investigation

Use [Stage 0](stage0/SKILL.md) when the goal, boundary, mechanism or useful next
observation is uncertain. Propose an explicit starting account, keep its omissions
visible, and revise it when evidence returns. An observation plan is not an obtained
finding or collection authority. Solver handoffs depend on exact investigation
revisions and must be revisited when supporting evidence changes.

A sufficiently specified static comparison can route directly to a cluster. Stage 0
is optional investigation support, with no mandatory systems, causal or dynamics
sequence. Its six fields describe the current account and next step; they do not
require a numeric recommendation or supersede the solver's readiness report.

## Which cluster for which job

| Job | Cluster | One-line trigger |
|---|---|---|
| Decide when to stop searching and commit to an option | [references/clusters/c01-optimal-stopping.md](references/clusters/c01-optimal-stopping.md) | "when do I stop looking," secretary problem, 37% rule, threshold rule, house-selling/parking, recall/rejection |
| Rank or score alternatives against several objectives/attributes, certain or uncertain | [references/clusters/c02-multiple-objectives.md](references/clusters/c02-multiple-objectives.md) | multiattribute utility, value function, preferential/utility independence, scaling constants, risk aversion, additive vs. multiplicative |
| Choose an action or plan over time under known/unknown dynamics, or update beliefs from evidence | [references/clusters/c03-sequential-decisions.md](references/clusters/c03-sequential-decisions.md) | MDP, POMDP, Bayes/belief update, Bellman equation, value iteration, Q-learning, MCTS |

If a request spans jobs, consult the relevant clusters and the capability registry. No automatic engine composition is implemented. Return the unresolved interface and a useful next observation or separate comparison.

## Input contract (translate explicit evidence; preserve unresolved fields)

1. **Horizon**: fixed known \(n\); fixed unknown with distribution (e.g. uniform on \([1,n_{max}]\)); open-ended/stochastic stop probability \(p\); finite-horizon sum; infinite-horizon discounted (\(\gamma\)) or average return.
2. **Feasible alternatives/states/actions**: set \(A\) (multi-objective case), or \(\mathcal{S}\), \(\mathcal{A}\) (sequential case), or the candidate stream (stopping case).
3. **Objective hierarchy and attribute ranges**: decomposition into attributes \(X_1,\ldots,X_n\), each with an explicit, recorded \([\text{worst},\text{best}]\) range spanned by the feasible alternatives.
4. **Subjective constraints/preferences**: preferential/utility independence assumptions (verified, not assumed), monotonicity direction per attribute, dominance pruning.
5. **Uncertainty models/prior/observations**: for stopping, ordinal-only vs. cardinal/full information; for sequential decisions, \(T\), \(R\), observation model \(O\) (POMDP), prior belief \(b_0\), observation stream.
6. **Search costs/recall/rejection**: per-look or per-offer cost; whether recall is possible and with what acceptance probability; whether an accepted offer can be rejected and with what probability.
7. **Risk attitude**: averse/neutral/prone, and constant/decreasing/increasing in attribute level (symmetric-lottery/fractile test, cluster 02 Sec. 4).
8. **Computational budget/tolerance**: exact finite-\(n\) enumeration vs. asymptotic approximation; iteration cap `k_max` or residual tolerance \(\delta\); MCTS simulations \(m\) or search depth \(d\); consistency-audit tolerance.

Ask only for rule-dependent prerequisites. A labelled scenario may support exploration; it cannot establish factual support. `missing_fields` preserves explicit false and zero. Do not demand a horizon for a static offer comparison.

## Output contract (every answer must report all applicable fields)

1. **Chosen action/stop decision**: the index/value to accept, or the action \(a^{*}\) to execute now.
2. **Unified zero-order formula used**: the exact named formula (e.g., Threshold Rule, additive value function, Bellman optimality equation), with cluster and section cited.
3. **Belief/value/threshold**: current belief vector \(b\) (if applicable), the value \(U(s)\), \(Q(s,a)\), or \(P_n(r)\) achieved, and the numeric threshold/cutoff used.
4. **Assumptions**: full input-contract values assumed or elicited, stated explicitly, so the answer is auditable and non-transferable to a different assumption set.
5. **Sensitivity**: how the decision changes if a stated assumption (horizon, recall/rejection probability, risk attitude, discount \(\gamma\)) is perturbed; flag fragility.
6. **Audit failures**: any validation invariant (below) that failed, with the specific residual and implicated response/quantity.

## Hard preconditions (check before dispatch; violating these invalidates the corresponding cluster's formulas)

- **Cluster 01**: a stopping rule exists only if the expected payoff at the best conceivable stopping point is finite; diverging-expectation games (e.g., triple-or-nothing) have no optimal stopping rule and must be handled by a different framework (e.g., fractional-bankroll rules).
- **Cluster 02**: the additive value/utility form requires mutual (or, for \(n=3\), pairwise) preferential or utility independence, verified by an explicit indifference test, not assumed for simplicity. "Verified" means the assumption registry covers **every proper nonempty subset** of the attribute set against its complement (c02 §7.3) — one recorded pair among many is not coverage. Note the flip test (c02 §7.5) does **not** establish independence; it discriminates additive from multiplicative *within* an already-verified structure, and raises if run before it. Scaling constants are only interpretable jointly with the attribute ranges they were assessed against.
- **Cluster 03**: the Markov assumption must hold (next state depends only on current state and action); Bellman-backup convergence requires \(\gamma \in [0,1)\) and bounded rewards; static belief updates require a normalized prior and a supported likelihood model. Zero-likelihood evidence has no posterior: inspect the observation or model. Dynamic filtering and POMDP planning are not implemented.

## The five stages

Help the user connect their situation to a supported model and inspect what the result
depends on. **The host owns Stages 0, 1 and 5** (interpretation and conversation); the
library owns Stages 2 through 4 (validation, computation and audit). Call the engine
for numerical results and retain useful labelled scenarios when readiness is unresolved.

### Stage 1: clarify consequential uncertainties and preserve exploration

"I want the best job" leaves the objective unresolved. Explain which concrete tradeoff
or observation would help. Offer a labelled scenario or bounded comparison when useful;
do not manufacture an actionable answer or demand irrelevant information.

```python
contract = InputContract()                      # nothing assumed
while (q := next_question(contract)) is not None:
    ...  # put q to the user verbatim; record ONLY what they actually say
```

- `classify_job(contract)` decides *which* job this is **from contract fields only**. If the
  fields do not determine it, it raises `ContractIncomplete(field='job')` rather than
  guessing. Never classify from the user's wording — "options", "best", "choose" tell you
  nothing about whether there is a stream to stop, a set to rank, or a policy to plan.
- `missing_fields(contract)` is the full remaining checklist; `next_question(contract)` is
  the next single question in dependency order.
- **Do not fill a field the user did not speak to.** An assumption the user never made is
  the exact failure this system exists to prevent. If they say "about twenty candidates,"
  that is not `n=20` — ask whether the number is fixed and known.
- The three checkpoints that decide everything, and that users never volunteer: the
  **horizon** (is \(n\) fixed, unknown-but-bounded, or open-ended?), the **information type**
  (ordinal ranks or cardinal scores?), and the **hard constraints** (can you recall a
  passed-over option? can an accepted offer decline?).

**Start with a decision description.** Record the question, concrete options and actions,
information types, objectives, time structure, uncertainties and constraints before
translating to an engine contract. `DecisionDescription`, `TranslationRecord` and
`translate_decision` retain the source input IDs, interpretation and rule for each field.
Keep physical measurements, evaluative scales and stopping-rule percentiles separate.
Negotiation availability does not determine measurement type. An equilibrium or cycle
is not the user's objective. Accumulation alone does not determine the horizon.

A static comparison routes directly to `static_comparison`; it needs no invented stock,
flow or causal diagram. If actions change future states, consider `discounted_mdp`.
If the question concerns intervention effects, the library has no causal inference engine.
Expose that missing interface and request appropriate causal evidence or a separate model.

**Screening is bounded evidence.** `overturn_test` reports `changes_decision`,
`stable_within_tested_bounds`, or `untested`. Inspect every probe's execution status.
A failed or unsupported probe does not establish action stability. Sequential probes
compare the full policy. Same-model changes can reverse an action.

```python
plan = elicitation_plan(contract)
plan["required"]
plan["load_bearing"]
plan.get("stable_within_tested_bounds", [])
plan.get("untested", [])
# droppable is retained for compatibility and is empty after finite screening.
```

**Preferences are revisable and scoped.** Use concrete offers or schedules to explore
tradeoffs. Preserve partial rankings and plausible weight ranges when a point value is
premature. A user may adopt a preference for this decision without making a standing
second-order commitment. `PreferenceRevision` records exploratory, decision-specific,
standing or suspended scopes. Reuse explicit adoption within scope without asking again.
A revision keeps history and invalidates dependent reports through `DecisionSession`.
Never relax a non-negotiable constraint to force a winner.

**Host evidence boundary.** Only the authorized host can supply interaction-event IDs.
A solver must never manufacture adoption. Record origin separately from acceptance:
measurements, user reports, external sources, model proposals and derived inputs differ.
"Just assume it" creates `scenario_branch`, with proposed, scenario-only overrides.
User adoption establishes intended use, not empirical truth. Preserve source references,
uncertainty, scope and derivation dependencies through copying and export.

### Stage 2 — Verification: reject premises that break the mathematics

Before a single equation loads, the library checks the user is not asking for something
impossible. `verify_preconditions(contract)` — or just `dispatch()`, which calls it — raises
rather than computing:

| Raise | Means | What you say |
|---|---|---|
| `NoOptimalStoppingRuleExists` | Expected payoff at the best stopping point diverges (triple-or-nothing with full re-wagering). | **No stopping rule exists.** Not "stop early" — *none exists*. Point at a bankroll-fraction framework (Kelly). |
| `IndependenceNotVerified` | The additive/multiplicative form was requested without covered independence. | Name the uncovered subsets and run the protocol below. |
| `NonMarkovProcess` | Next state depends on deep history. | Augment the state until it doesn't, or refuse. |
| `UnclassifiedVariant` | The corpus has no row for this assumption set. | Say so plainly. **Never supply a constant from memory.** |

**The independence protocol (the "flip test" checkpoint).** For a multiattribute job you must
prove independence before any additive or multiplicative form is legal. Two separate steps,
in this order — the corpus is emphatic that they are not the same test:

```python
# 2a. Coverage. Mutual independence needs EVERY proper nonempty subset verified
#     against its complement (c02 §7.3). One recorded pair is not coverage.
for subset, complement, question in independence_questions(contract):
    answer = ...                                  # put `question` to the user
    contract.independence_assumptions.append(
        record_independence(subset, complement, contract.independence_kind,
                            verified=answer, evidence="...")
    )

# 2b. Form. ONLY once 2a is covered, the flip test discriminates additive from
#     multiplicative WITHIN that structure (c02 §7.5). It never establishes
#     independence, and run_flip_test raises if you try to use it that way.
contract.flip_test_performed = True
contract.flip_test_preferred_pairing = ...        # None | 'straight' | 'crossed'
```

Ask 2b with `FLIP_TEST_QUESTION`. If the recorded flip test disagrees with the form implied
by \(\sum k_i\), that is an **INV-3 audit failure**, not something to average away — the
elicitation is internally inconsistent and the user has to resolve it (c02 §7.8).

### Stage 3 — Computation: the conversation stops, the engine runs

```python
report = dispatch(job, contract)     # verify -> select -> compute -> audit -> report
```

You do not choose the formula; the elicited assumption set does, via `CALIBRATIONS`
(one entry per row of c01's Decision Table). Every constant is locked to the assumption set
it was derived under. **Never reuse 37%, 0.58, 0.61, or 0.25 outside its calibrated row** —
the library will refuse, and so should you.

### Stage 4 — Audit: the engine proves its own work before you see it

`dispatch()` runs the validation invariants and raises `AuditFailure` rather than returning a
decision that failed them. A passing computation with a failing invariant is not an answer.

`AuditFailure` tells you where to loop back to — use it, do not restart the interrogation:

```python
except AuditFailure as e:
    e.invariant_ids   # ['INV-3'] — which invariant failed
    e.invariants      # the InvariantResult objects, each with a diagnostic message
    e.fields          # ['independence_assumptions', ...] — exactly what to re-elicit
    e.remedy          # ready-to-speak instruction
```

Re-ask **only** `e.fields`. Then re-run. This is the Stage 4 → Stage 1 loop.

### Stage 5: report the computation and readiness separately

```python
print(report.to_markdown())
report.computation
report.assumption_support
report.readiness
report.execution_note
```

Show the computed action, formula, citation, assumptions, numerical termination,
required-check coverage, sensitivity domain and readiness together. `exploratory`
means a scenario; `conditional` means required support or uncertainty treatment remains
unresolved; `ready_under_stated_conditions` is scoped and revisable; `blocked` means
there is no usable recommendation under the current checks or feasibility conditions.
Readiness never authorizes an external action.

A Bellman contraction diagnostic is not convergence. Report the returned-value residual
and its value-error bound, with the finite bounded discounted MDP assumptions. A
budget-limited result remains provisional. Same-model corrections may change actions.
Do not turn `analysis_is_complete` into a universal stopping instruction: it is deprecated.

Explain what could reopen the decision: preference revision, changed observations,
changed deadline, violated feasibility or model conditions. If further investigation
has a cost, describe the tradeoff and record a scoped choice under residual uncertainty.
Do not claim that uncertainty disappeared. Ask only questions connected to a consequential
uncertainty, model choice, feasibility or preference. When a supported explicit domain
establishes equivalence, avoid demanding unnecessary precision.

## Minimal Socratic elicitation loop

Ask only what is missing. `next_question()` returns them in dependency order, so the
authoritative sequence is whatever the library hands back — this table is the human-readable
mirror of `QUESTION_BANK` in `src/dominant_circuit/core/elicit.py`, and the two are kept in
sync by `tests/test_corpus.py::test_skill_question_bank_parity`.

Each row names the **contract field** it fills. Never fill a field the user did not speak to.

| # | Question | Contract field |
|---|---|---|
| 1 | "Is this a stopping problem, a multi-objective ranking, or a sequential plan?" | `job` |
| 2 | "Is the total number of options/time fixed and known, fixed but unknown, open-ended/stochastic, or unbounded?" | `horizon` |
| 3 | "What is the exact pool size n?" | `n` |
| 4 | "What is the upper bound n_max on the unknown pool size?" | `n_max` |
| 5 | "What is the per-step probability that the opportunity stream ends?" | `stop_prob_per_step` |
| 6 | "What is the payoff structure: best-or-nothing, net-value-minus-cost, ruin-risk, multiattribute, or discounted return?" | `payoff` |
| 7 | "Does the expected reward grow without bound if you never stop (e.g. triple-or-nothing with full re-wagering)?" | `payoff_diverges` |
| 8 | "Can you only compare options relatively (ordinal) or do you have absolute scores (cardinal)?" | `information` |
| 9 | "Once you pass on an option, can you revisit it later?" | `recall_allowed` |
| 10 | "If you recall a past option, what is the probability it is still available?" | `recall_accept_prob` |
| 11 | "What is the probability that an accepted offer is declined by the candidate?" | `rejection_prob` |
| 12 | "What is the per-look cost, normalized to the [0,1] outcome scale?" | `search_cost` |
| 13 | "What is the per-trial probability q that a trial succeeds rather than wiping out everything accumulated?" | `ruin_success_prob` |
| 14 | "What is the average gain m per successful trial?" | `ruin_mean_gain` |
| 15 | "What are the attributes and their explicit [worst, best] ranges?" | `attributes` |
| 16 | "Has mutual (or pairwise) utility/preferential independence been verified, and against which attribute subsets?" | `independence_assumptions` |
| 16b | "In the two 50-50 gambles built from the same outcomes, do you prefer the 'straight' pairing, the 'crossed' pairing, or are you indifferent?" | `flip_test_preferred_pairing` |
| 17 | "What are the scaling constants k_i, each attached to its assessed range?" | `scaling_constants` |
| 18 | "Is the decision maker risk-averse, risk-neutral, or risk-prone?" | `risk_attitude` |
| 19 | "Does the next state depend only on the current state and your action, or does the earlier history matter?" | `markov_verified` |
| 20 | "What discount factor γ ∈ [0,1) should be used?" | `gamma` |

Two of these are **hard-required** by `missing_fields()` and are the ones most often skipped:
`payoff_diverges` (row 7) gates every stopping problem — a diverging payoff means *no optimal
stopping rule exists*, not a smaller cutoff — and `markov_verified` (row 19) gates every
sequential problem. Ask them; do not assume the benign answer.

**Combinations the corpus does not cover.** Some assumption sets are individually valid but
jointly uncalibrated; `dispatch()` raises `UnclassifiedVariant` rather than picking whichever
branch is tested first. Report that plainly — do not supply a constant from memory:

- **Recall *and* rejection risk both active.** c01 §7's Invariant is explicit that the two move
  the look/leap boundary in opposite directions (0.61 up, 0.25 down); the Decision Table has no
  joint row.
- **Cost-of-search with ordinal-only information.** c01 §9 is derived under full information.
- **Cardinal information with anything but a fixed, known n.** The Threshold Rule's ≈58% is
  calibrated for Decision Table row 2; the unknown-n and stochastic-termination rows are
  ordinal-only.

## Core formulas (exact, by cluster)

> **Reference only.** These are for recognition and explanation. Any number reported to a user must come from `dispatch()`. If you computed by hand because no interpreter was available, label the result **UNAUDITED** and name the invariants that were not checked.

**Multiattribute value/utility (cluster 02).** Additive, valid only under verified mutual/pairwise preferential (certainty) or utility (uncertainty) independence, weights summing to 1:
\[
v(x_1,\ldots,x_n) = \sum_{i=1}^n \lambda_i v_i(x_i), \qquad u(x_1,\ldots,x_n) = \sum_{i=1}^n k_i u_i(x_i), \qquad \sum_i k_i = 1.
\]
Multiplicative, when mutual utility independence holds but \(\sum_i k_i \ne 1\):
\[
1 + k\,u(x) = \prod_{i=1}^n \bigl(1 + k\,k_i\,u_i(x_i)\bigr), \qquad 1+k=\prod_{i=1}^n(1+k k_i).
\]
Additive is the special case \(k=0\) (i.e. \(\sum_i k_i = 1\)) of the multiplicative form, not a separately-derived rule.

**Bayes update / POMDP belief update (cluster 03).**
\[
P(x\mid y) = \frac{P(y\mid x)P(x)}{P(y)}, \qquad b'(s') \propto O(o\mid a,s') \sum_s T(s'\mid s,a)\,b(s).
\]

**Bellman action selection (cluster 03).**
\[
Q(s,a) = R(s,a) + \gamma \sum_{s'} T(s'\mid s,a)\,U(s'), \qquad a^{*} = \arg\max_a Q(s,a), \qquad U^{*}(s) = \max_a Q(s,a).
\]

**Stop iff stop value \(\ge\) continuation value (cluster 01, general criterion underlying every stopping rule here).** At any decision point, stop (accept/leap) iff
\[
V_{\text{stop}} \ge V_{\text{continue}},
\]
where \(V_{\text{stop}}\) is the value of accepting now and \(V_{\text{continue}}\) is the expected value of continuing under the optimal future policy. Every rule in cluster 01 (Look-Then-Leap, Threshold Rule, cost-aware threshold, burglar ceiling) is this one criterion specialized to a payoff structure and information condition. **The 37% constant is what this criterion reduces to only under the classical secretary assumption set** (fixed known \(n\), ordinal-only, no recall, no rejection, best-or-nothing payoff); it is a special case, not the general formula. Change one assumption and the same criterion yields a different constant (58% full information, 25% rejection risk, 61% recall, or none at all under diverging payoffs); see cluster 01 Sec. 8.

## Compact orchestration (Python-computable)

```python
from dominant_circuit import (
    InputContract, Job, dispatch, classify_job,
    missing_fields, next_question,
    ContractIncomplete, PreconditionViolation, UnclassifiedVariant, AuditFailure,
)

# Stage 1 — elicit. The library never asks; the host asks.
contract = InputContract(job=Job.STOPPING)
while (q := next_question(contract)) is not None:
    ...  # host puts q to the user, records the answer on `contract`

# Stages 2-4 — verify, compute, audit. One call. Raises rather than guessing.
report = dispatch(Job.STOPPING, contract)

# Stage 5 — report.
print(report.to_markdown())          # computation, audit coverage and readiness
report.action                        # scoped model result
report.decision, report.formula_name, report.citation
report.numeric, report.assumptions, report.sensitivity, report.audit
report.readiness                    # scoped status, reasons and reopening conditions
report.assumptions_to_confirm        # ...once these facts are checked
```

The whole loop, including the Stage 4 → Stage 1 correction path:

```python
while True:
    while (q := next_question(contract)) is not None:
        ...  # ask q, record the answer
    try:
        report = dispatch(classify_job(contract), contract)
        break
    except ContractIncomplete as e:
        ...  # ask e.remedy, record, loop
    except AuditFailure as e:
        ...  # re-elicit ONLY e.fields, then loop
    except (PreconditionViolation, UnclassifiedVariant) as e:
        ...  # report e and e.remedy; this problem is not computable as stated
        raise
```

> **Host protocol (mandatory).**
> Drive elicitation with `missing_fields()` / `next_question()`. Do not fill contract fields on the user's behalf, and do not infer a value the user did not state — an assumption the user never made is the failure this system exists to prevent.
> `ContractIncomplete` carries `.field` and `.remedy`; put `.remedy` to the user and retry. Do not work around it.
> `PreconditionViolation` (and its subclasses `NoOptimalStoppingRuleExists`, `NonMarkovProcess`, `IndependenceNotVerified`) means the problem as stated is not computable. Report `.remedy`. Do not substitute a nearby problem that is computable.
> `UnclassifiedVariant` means the corpus does not cover this assumption set. Say so plainly. **Do not supply a constant from memory.**
> `AuditFailure` means a validation invariant failed. Report the failed invariant IDs. Do not present the decision as actionable.
> If `import dominant_circuit` fails, say that the engine is unavailable and that any figure you give is unaudited. Do not compute silently in prose.

## Worked interaction: exploration with explicit assumptions

> **User:** I have 50 interviews. I can rank candidates. There is no recall.
> **Host:** Can an offer be declined? That changes the applicable stopping rule.
> **User:** Just assume they accept for now. I want the best of these 50.

Record `n=50`, fixed-known horizon, ordinal information, best-or-nothing payoff,
`recall_allowed=False`, and finite payoff. The proposed `rejection_prob=0.0` is a
scenario input, not an observation. The scenario computes the classical finite-n rule.

> **Host:** Conditional model result: {'look_until': 18, 'leap_from': 19, 'n': 50}.
> In this scenario the rule rejects the first 18 of 50 while recording the best.
> From #19 onward, it accepts the first candidate better than that opening group.
> Formula: Look-Then-Leap (exact finite-n), `c01 §4.1`. r\* = 19, P = 0.3743.
> Rejection risk remains unresolved; this calculation does not establish readiness.

If rejection later becomes a supported 50% input, recompute under its calibrated row.
Do not change the historical scenario or silently reuse its readiness. For a fuller
preference exploration, adoption and reopening flow, run
[examples/reflective_decision.py](examples/reflective_decision.py).

## Validation invariants (cross-cluster)

1. **Assumption-set match.** The constant/rule dispatched must correspond exactly to the elicited horizon/information/recall/rejection combination; reusing 37%, 58%, 61%, or 25% outside their calibrated assumption set is an audit failure.
2. **Normalization.** Every probability, belief, or component value/utility function must satisfy its stated normalization (\(\sum=1\), \(v(\text{worst})=0\), \(v(\text{best})=1\)) before use downstream.
3. **Independence verified, not assumed.** No additive or multiplicative multiattribute form may be used without a recorded, verified independence test (cluster 02 flip test or equivalent).
4. **Bellman fixed point.** After convergence, \(U(s) = \max_a Q(s,a)\) must hold to within declared tolerance \(\delta\); Bellman residuals must shrink by a factor no worse than \(\gamma\) per sweep.
5. **Range-fixed weights.** No scaling constant \(k_i\)/\(\lambda_i\) may be recorded without an attached, explicit attribute range; reusing one elicited under a different range is invalid.
6. **Finite-expectation precondition.** No stopping rule may be applied to a payoff structure with diverging expected value at the best stopping point.
7. **Overdetermination.** Report coverage when available. INV-7 is advisory; it neither proves empirical independence nor gates unrelated computations.

## Anti-cargo-cult rules

- Never state "37%" as a universal answer to "when should I stop." It is the exact limit of \(P_n(r)\) under one specific assumption set (fixed known \(n\), ordinal-only, no recall, no rejection, best-or-nothing); state the assumption set alongside the number, every time.
- Never label a scaling constant \(k_i\) as an "importance weight" without citing the attribute range it was assessed against.
- Never adopt the additive multiattribute form because it is simpler; adopt it only after the independence test passes.
- Never treat an inconsistent elicitation response as noise to average away; surface it to the user and re-elicit.
- Never skip dominance screening before running full preference elicitation on a candidate set.
- Never apply a Bellman/MDP method to a non-Markov process without first re-deriving or augmenting the state to restore the Markov property.
- Never report a decision without its audit results; a passing computation with a failing invariant is not a valid answer.
