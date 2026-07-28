---
name: dominant-circuit
description: "Master decision-mechanics router for choosing when to stop a search, how to trade off multiple objectives under certainty or uncertainty, and how to select or time actions in sequential/uncertain environments. Use when the user asks when to stop looking or searching, how to decide among finitely many alternatives with competing objectives, how to weigh tradeoffs or set scaling constants/utility weights, how to update beliefs with new evidence (Bayes/POMDP), how to pick an action under a Markov Decision Process or Bellman framework, or invokes phrases like optimal stopping, secretary problem, 37% rule, satisficing threshold, multiattribute utility, preferential/utility independence, expected utility, risk aversion, MDP, POMDP, belief update, value iteration, Q-learning, or Monte Carlo tree search. Not for open-ended brainstorming or single-attribute certainty comparisons with no search, tradeoff, or sequential/uncertainty structure."
---

# Dominant-Circuit

Master router over three zero-order decision-mechanics clusters. This file dispatches, it does not restate the math. Open the linked cluster file before computing.

## When to use

Use when a request has **decision structure**, not just a question:
- A search/queue of options must be stopped at some point ("when do I stop looking/interviewing/dating/selling/renting").
- Multiple competing objectives/attributes must be traded off into one ranking or score ("which alternative is best given cost, quality, risk...").
- An action must be chosen now that affects a future state under known/unknown dynamics, or beliefs must be updated from observations ("what should I do next," "update my belief," "plan a sequence of moves").

Not for single-criterion lookups, open-ended ideation, or anything with no explicit alternatives/objective/uncertainty structure.

## Which cluster for which job

| Job | Cluster | One-line trigger |
|---|---|---|
| Decide when to stop searching and commit to an option | [references/clusters/c01-optimal-stopping.md](references/clusters/c01-optimal-stopping.md) | "when do I stop looking," secretary problem, 37% rule, threshold rule, house-selling/parking, recall/rejection |
| Rank or score alternatives against several objectives/attributes, certain or uncertain | [references/clusters/c02-multiple-objectives.md](references/clusters/c02-multiple-objectives.md) | multiattribute utility, value function, preferential/utility independence, scaling constants, risk aversion, additive vs. multiplicative |
| Choose an action or plan over time under known/unknown dynamics, or update beliefs from evidence | [references/clusters/c03-sequential-decisions.md](references/clusters/c03-sequential-decisions.md) | MDP, POMDP, Bayes/belief update, Bellman equation, value iteration, Q-learning, MCTS |

If a request spans jobs (e.g., "stop searching once expected multiattribute utility falls below a threshold"), read all relevant clusters and compose per the Unified Pipeline below.

## Input contract (elicit or infer every field before computing)

1. **Horizon**: fixed known \(n\); fixed unknown with distribution (e.g. uniform on \([1,n_{max}]\)); open-ended/stochastic stop probability \(p\); finite-horizon sum; infinite-horizon discounted (\(\gamma\)) or average return.
2. **Feasible alternatives/states/actions**: set \(A\) (multi-objective case), or \(\mathcal{S}\), \(\mathcal{A}\) (sequential case), or the candidate stream (stopping case).
3. **Objective hierarchy and attribute ranges**: decomposition into attributes \(X_1,\ldots,X_n\), each with an explicit, recorded \([\text{worst},\text{best}]\) range spanned by the feasible alternatives.
4. **Subjective constraints/preferences**: preferential/utility independence assumptions (verified, not assumed), monotonicity direction per attribute, dominance pruning.
5. **Uncertainty models/prior/observations**: for stopping, ordinal-only vs. cardinal/full information; for sequential decisions, \(T\), \(R\), observation model \(O\) (POMDP), prior belief \(b_0\), observation stream.
6. **Search costs/recall/rejection**: per-look or per-offer cost; whether recall is possible and with what acceptance probability; whether an accepted offer can be rejected and with what probability.
7. **Risk attitude**: averse/neutral/prone, and constant/decreasing/increasing in attribute level (symmetric-lottery/fractile test, cluster 02 Sec. 4).
8. **Computational budget/tolerance**: exact finite-\(n\) enumeration vs. asymptotic approximation; iteration cap `k_max` or residual tolerance \(\delta\); MCTS simulations \(m\) or search depth \(d\); consistency-audit tolerance.

If any field is missing, run the Socratic elicitation loop below before computing; never silently default to the classical 37%-style assumption set.

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
- **Cluster 03**: the Markov assumption must hold (next state depends only on current state and action); Bellman-backup convergence requires \(\gamma \in [0,1)\) and bounded rewards; belief updates require a well-defined observation model and must reset to uniform on zero-likelihood evidence rather than divide by zero.

## The five stages

The user is not chatting. They are plugging a problem into a centrifuge. Your job across
these five stages is to strip the vibes off their dilemma and show them the constants
underneath. Each stage has an owner: **you own Stages 1 and 5** (the conversation), **the
library owns Stages 2–4** (the physics). Never do the library's job in prose.

### Stage 1 — Elicitation: refuse to compute until the boundary conditions are locked

Humans arrive vague. "I want the best job" is not a problem statement; it is a mood.
**Halt. Do not compute. Interrogate.**

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

**先问权重，再问真假 — ask weight before truth.** Details are infinite; "what else haven't I
considered?" never terminates. Only one question terminates, and it is the **overturn test**:

> Is the presence or absence of this factor sufficient to overturn my current conclusion?

If not, it is a high-order small quantity — throw it out of the dominant equation and **do not
spend the user's attention on it.**

```python
plan = elicitation_plan(contract)
plan["required"]      # ask these — no conclusion exists yet
plan["load_bearing"]  # passed the overturn test; worth asking about
plan["droppable"]     # failed it. DO NOT ASK. It cannot change the answer.

overturn_test(contract, "recall_allowed").verdict   # the reasoning, per factor
```

Two rules on using it:

- **Weight has three prerequisites and they are never screenable.** 给定目标、时间尺度、比较对象 —
  the goal, the time scale, the comparison set (`WEIGHT_PREREQUISITES`). A factor has no weight
  until there is an objective function to weigh it against, so `overturn_test` *raises*
  `ContractIncomplete` rather than inventing a baseline. Ask `plan["required"]` first; screening
  only becomes possible once a conclusion exists to test against.
- **There is no standard answer for weight; it depends entirely on the objective function.**
  The same factor genuinely goes both ways: for n=50, "exact computation or the famous 37%?"
  changes the answer (19 vs 18) and is load-bearing; for n=45 both give 17, so the question is
  a 舍去项 and asking it wastes the user's time. Never carry a fixed list of "important
  factors" between conversations — screen against *this* goal.

**A refusal counts as an overturn.** If setting a factor makes the problem uncalibrated, that
factor is emphatically load-bearing, not neutral.

**The user owns the goal; you only help them see it.** You may coach — lay out what a goal
would have to specify, offer candidate framings, point out that "the best job" is not yet an
objective function. You may not decide it. `classify_job` reads contract fields, never prose,
for exactly this reason: the moment the AI picks the objective function, every weight downstream
is the AI's opinion wearing the user's name.

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

### Stage 5 — Reporting: the zero-order truth, and permission to stop

```python
print(report.to_markdown())          # all six Output Contract fields + Execute
```

Report `report.action` as the recommendation — it is the decision as an instruction, not the
raw dict. Always show the formula name and `citation` next to the number, and state the
assumptions that make the action valid, because the answer is **not transferable** to a
different assumption set.

Report the answer as a **zero-order expansion** (零阶展开), not a bare number — this is what
lets a user see which assumptions are load-bearing:

```python
report.zero_order        # 零阶: the trunk
report.corrections       # 一阶修正: refine it, cannot overturn it
report.overturns         # 翻盘: a DIFFERENT trunk — this is the flip test's answer
report.dropped           # 舍去项: thrown away by 主导平衡
report.hard_constraints  # 硬约束: conditions under which no trunk exists
```

`corrections` vs `overturns` is decided structurally, not by size: a term is a correction when
it refines the same calibrated model, an overturn when it moves to a different row of the
corpus decision table. **Do not re-sort them by magnitude** — for n=50 the +6% term is a
correction and the −33% term is an overturn. Presenting recall or rejection as a "small
adjustment to the 37% rule" is precisely the cargo-cult error this system exists to prevent.

Then answer the question users actually have: *may I stop thinking about this?*

```python
report.analysis_is_complete    # bool — no further computation can improve this
report.assumptions_to_confirm  # facts to check; wrong ones change the decision
report.execution_note          # the above, in a sentence you can say out loud
```

`analysis_is_complete` being `True` means the remaining risk is **factual, not analytical**:
more deliberation cannot help, only checking the world can. Say so. Telling a user they may
stop analyzing and start executing is part of the deliverable, not a courtesy.

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
print(report.to_markdown())          # six Output Contract fields + Execute
report.action                        # the decision as an instruction
report.decision, report.formula_name, report.citation
report.numeric, report.assumptions, report.sensitivity, report.audit
report.analysis_is_complete          # may the user stop analyzing?
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

## Worked interaction: vague input to executable answer

What the five stages look like in practice. Note where the AI refuses.

> **User:** I've been interviewing people for a role and I want to hire the best one. When should I stop?

**Stage 1 — halt and interrogate.** No number yet. `classify_job` cannot even name the job
from "hire the best one," and `next_question` asks for the horizon:

> **AI:** Before I can compute anything I need three boundary conditions. First: is the total
> number of candidates fixed and known, fixed but unknown, or open-ended?
>
> **User:** I have 50 scheduled. That's all of them.
>
> **AI:** Second: as each candidate finishes, can you only rank them against the ones you've
> already seen, or do you have an absolute score for each on a scale you trust?
>
> **User:** Just relative. I can say who was better, not put a number on it.
>
> **AI:** Third: once you pass on a candidate, can you go back to them later? And can a
> candidate you offer turn *you* down?
>
> **User:** No going back. And assume they'd accept.
>
> **AI:** Last one, and it matters more than it sounds: does the value of the outcome grow
> without bound the longer you keep searching?
>
> **User:** No, I just want the best of the 50.

Contract complete: `horizon=FIXED_KNOWN, n=50, information=ORDINAL,
payoff=BEST_OR_NOTHING, recall_allowed=False, payoff_diverges=False`.
**Nothing was inferred.** "That's all of them" was confirmed as fixed-and-known, not assumed.

**Stages 2–4 — `dispatch(Job.STOPPING, contract)`.** Preconditions pass. The assumption tuple
matches exactly one row of c01's Decision Table, so the exact finite-\(n\) argmax runs (c01
§4.1), not the asymptotic 37% shortcut. INV-1 confirms the constant is locked to the elicited
set; INV-6 confirms finite expectation. Audit passes.

**Stage 5 — report and release.**

> **AI:** **Reject the first 18 of 50 outright, whatever they look like, while recording the
> best you see. From #19 onward, accept the first one that beats every candidate in that
> opening block. If none does, you are forced to take #50.**
>
> Formula: Look-Then-Leap (exact finite-n), `c01 §4.1`. r\* = 19, P = 0.3743.
>
> This holds *because* n is fixed at 50, you have ordinal information only, there is no
> recall, and no rejection risk. Change any one of those and the number changes — with recall
> at 50% it would be 0.61·n, not 0.37·n.
>
> **You can stop analyzing.** No further calculation improves this. Two things move the
> number if they are wrong: whether you can really not go back to a passed-over candidate,
> and the exact-vs-asymptotic computation (the famous "37% rule" would have said 18 here;
> the exact finite-*n* argmax says 19, and for n=50 exact is worth having). If the recall
> answer changes, come back — the cutoff moves a lot.

Note the AI reports **19**, not `round(50/e) = 18`. The 37% figure is the asymptotic limit,
not the answer for a finite pool; the library computes the exact argmax by default and the
host must not "round it to the famous number."

Contrast the refusal path. Had the user said "I'd let the pool run until I find someone, and
each round I double down on the search budget," `payoff_diverges=True` yields
`NoOptimalStoppingRuleExists` and the correct answer is not a later cutoff but:

> **AI:** There is no optimal stopping rule for this problem. When the expected payoff at the
> best conceivable stopping point diverges, no threshold caps optimal behavior at a finite
> point, and "always continue" leads to ruin (c01 §8). This needs a bankroll-fraction
> framework such as Kelly, not a stopping rule. I am not going to give you a cutoff number.

## Validation invariants (cross-cluster)

1. **Assumption-set match.** The constant/rule dispatched must correspond exactly to the elicited horizon/information/recall/rejection combination; reusing 37%, 58%, 61%, or 25% outside their calibrated assumption set is an audit failure.
2. **Normalization.** Every probability, belief, or component value/utility function must satisfy its stated normalization (\(\sum=1\), \(v(\text{worst})=0\), \(v(\text{best})=1\)) before use downstream.
3. **Independence verified, not assumed.** No additive or multiplicative multiattribute form may be used without a recorded, verified independence test (cluster 02 flip test or equivalent).
4. **Bellman fixed point.** After convergence, \(U(s) = \max_a Q(s,a)\) must hold to within declared tolerance \(\delta\); Bellman residuals must shrink by a factor no worse than \(\gamma\) per sweep.
5. **Range-fixed weights.** No scaling constant \(k_i\)/\(\lambda_i\) may be recorded without an attached, explicit attribute range; reusing one elicited under a different range is invalid.
6. **Finite-expectation precondition.** No stopping rule may be applied to a payoff structure with diverging expected value at the best stopping point.
7. **Overdetermination.** Elicitation must gather more indifference/trade-off equations than free parameters so inconsistency is detectable, not just assumed away.

## Anti-cargo-cult rules

- Never state "37%" as a universal answer to "when should I stop." It is the exact limit of \(P_n(r)\) under one specific assumption set (fixed known \(n\), ordinal-only, no recall, no rejection, best-or-nothing); state the assumption set alongside the number, every time.
- Never label a scaling constant \(k_i\) as an "importance weight" without citing the attribute range it was assessed against.
- Never adopt the additive multiattribute form because it is simpler; adopt it only after the independence test passes.
- Never treat an inconsistent elicitation response as noise to average away; surface it to the user and re-elicit.
- Never skip dominance screening before running full preference elicitation on a candidate set.
- Never apply a Bellman/MDP method to a non-Markov process without first re-deriving or augmenting the state to restore the Markov property.
- Never report a decision without its audit results; a passing computation with a failing invariant is not a valid answer.
