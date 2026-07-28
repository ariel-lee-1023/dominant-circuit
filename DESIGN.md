# DESIGN.md — The Dominant-Circuit Interaction Model

The product design, stated by stage of human–AI interaction. `SPEC.md` says how the code is
built; this says what the interaction is *for*. Where they disagree about mechanics, `SPEC.md`
and `SPEC-2-PUNCHLIST.md` win; where a reader wants to know *why* a refusal is a feature, this
document wins.

---

## Purpose

When a human sits down with this AI, they are not chatting with a friend. They are plugging
their problem into a mathematical centrifuge. The interface is designed to strip away the
user's cognitive biases and force them to look at the raw physical constants of their decision.

The corollary, and the thing most easily lost in maintenance: **the refusals are the product.**
An AI that always returns a number is worthless here, because most vaguely-posed decision
questions do not have one. Every `raise` in this library is a designed output, not an error
path.

## Stage ownership

| Stage | Owner | Code |
|---|---|---|
| 1. Elicitation | **Host AI** | `core/elicit.py` |
| 2. Verification | Library | `core/verify.py`, `engines/multiobjective.py` |
| 3. Computation | Library | `core/dispatch.py` → `engines/` |
| 4. Auditing | Library | `core/audit.py` |
| 5. Reporting | **Host AI** | `core/report.py` |

The library is pure and non-interactive. It performs no I/O and asks no questions. The host
owns both ends of the conversation; the library owns the physics in the middle. A host that
computes in prose instead of calling the library has defeated the entire design.

---

## Stage 1 — Elicitation (the Socratic interrogation)

Humans are naturally vague; they want to talk about "feelings" and "vibes." The AI's first job
is to **refuse to compute until the boundary conditions are locked in.**

- **Mechanism.** The AI acts as a strict investigator. If the human says "I want the best job,"
  the AI halts and demands parameters.
- **Checkpoints.** It forces the user to define the **time horizon** (is \(n\) fixed or
  infinite?), the **information type** (ordinal ranks vs. cardinal scores), and the **hard
  constraints** (can you recall a past option? can an accepted offer decline?).
- **Goal.** To translate a messy human dilemma into a rigid Input Contract.

**Entry points.** `next_question(contract)` for the next question in dependency order;
`missing_fields(contract)` for the whole remaining checklist; `classify_job(contract)` to
determine the job **from contract fields only**. Classification never reads user prose — that
was defect D-06, and inferring "stopping problem" from the word "options" is exactly the
mistake this system exists to prevent.

**The rule that matters most:** do not fill a field the user did not speak to. An assumption
the user never made is the failure this whole design targets.

## Stage 2 — Verification (the reality check)

Before a single equation is loaded, the AI must ensure the user isn't trying to break the laws
of physics.

- **Mechanism.** The AI runs the parameters against hard mathematical constraints.
- **Checkpoints.** If the user wants an additive utility formula, the AI forces them through
  the flip test to prove their variables are actually independent. If the user is analyzing a
  game with diverging expected payoffs (a double-or-nothing bet that goes on forever), the AI
  rejects the premise entirely.
- **Goal.** To prevent "cargo cult" computing, where the math looks right but the underlying
  assumptions are physically impossible.

**Entry points.** `verify_preconditions(contract)`, called for you by `dispatch()`. For the
independence checkpoint, in this order and not the other way round:

1. **Coverage** (c02 §7.3) — `independence_questions(contract)` returns each unverified claim
   as an askable question; `record_independence(...)` turns the answer into a registry entry.
   Mutual independence requires **every proper nonempty subset** verified against its
   complement. One recorded pair is not coverage.
2. **Form** (c02 §7.5) — only then does the flip test discriminate additive from multiplicative
   *within* that structure. `run_flip_test` raises if used before step 1. The flip test does
   not establish independence and never did.

## Stage 3 — Computation (the dominant balance)

Once the boundary conditions are set, the conversation stops and the physics engine takes over.

- **Mechanism.** The Python backend routes the validated inputs to the correct zero-order
  formula.
- **Checkpoints.** It drops the negligible terms and focuses solely on the dominant causal
  variables. It might apply the Look-Then-Leap threshold (\(r \approx n/e\)) for stopping
  problems, or run Bellman backups
  \(U^{*}(s) = \max_a\left(R(s,a) + \gamma\sum_{s'}T(s'|s,a)U^{*}(s')\right)\)
  for sequential planning.
- **Goal.** To find the one or two core feedback loops that actually control the outcome.

**Entry point.** `dispatch(job, contract)`. The elicited assumption set selects the formula via
`CALIBRATIONS`, one entry per row of c01's Decision Table. Constants are locked to the
assumption set they were derived under; asking for one outside its calibrated row raises
`UnclassifiedVariant` rather than returning a plausible figure.

Dominance screening runs first (`dominance_screen`, c02 §2.4): a dominated alternative cannot
win under any monotone value function, so eliciting preferences over it is wasted attention.

> **Naming note — `solvers.py`.** Earlier drafts of this design called the Stage 3 backend
> `solvers.py`. That file is not missing; it was **deliberately removed and replaced.**
> `SPEC.md` records it as the pre-rewrite module in baseline commit `a66504d` ("solvers.py,
> engine.py, main.py"), logs defects **D-12** (no sequential/MDP/POMDP code at all) and
> **D-13** (multiplicative form raised instead of computing) against it, and closes both by
> splitting the responsibility in two: **`core/dispatch.py`** routes, and the three solvers
> live in **`engines/`** — `stopping.py` (c01), `multiobjective.py` (c02), `sequential.py`
> (c03). See SPEC.md §1's stage table, which maps Stage 3 to "`core/dispatch.py` → `engines/`"
> precisely against the old `solvers.py`.
>
> So: read "solvers.py" in any older text as "`core/dispatch.py` plus the `engines/`
> package," and do not reintroduce the name.
> `tests/test_corpus.py::test_spec_layout_matches_the_package` enforces this.

## Stage 4 — Auditing (the self-correction)

The AI must prove its own work before showing it to the human. Nature cannot be fooled — as
Feynman put it — and the machine shouldn't fool itself either.

- **Mechanism.** The AI runs internal validation invariants.
- **Checkpoints.** Do all probabilities in the belief state sum perfectly to \(1.0\)? Did the
  Bellman residuals actually shrink by the discount factor \(\gamma\)? Is the constant that was
  dispatched calibrated for the assumption set that was elicited?
- **Goal.** If the math doesn't check out, the AI throws an error and loops back to Stage 1,
  forcing the user to fix their contradictory inputs.

**Entry points.** `dispatch()` runs the invariants and raises `AuditFailure` rather than
returning a decision that failed them. The exception carries the loop-back target, so Stage 4 →
Stage 1 re-asks the *specific* contradictory field instead of restarting:

```python
except AuditFailure as e:
    e.invariant_ids   # which invariants failed
    e.invariants      # each with a diagnostic message
    e.fields          # exactly what to re-elicit
```

INV-1…INV-6 are enforced. **INV-7 (overdetermination) is conditional and non-blocking** — a
passing report does not prove the elicitation was overdetermined. See `AGENTS.md`.

## Stage 5 — Reporting (the zero-order truth)

The AI delivers the unvarnished conclusion to the human.

- **Mechanism.** A clean, formatted output that separates the signal from the noise.
- **Checkpoints.** The AI explicitly lists the exact mathematical formula used, the recommended
  action, and — crucially — the physical assumptions that make this action valid. It also tells
  the user when they are allowed to stop analyzing and start executing.
- **Goal.** To give the user a mathematically optimal conclusion that they can actually trust
  and act upon.

**Entry points.** `report.to_markdown()` renders all six Output Contract fields plus an
`## Execute` section. Report `report.action` as the recommendation — the decision as an
instruction, not the raw dict. Always show `formula_name` and `citation` beside the number, and
state the assumptions, because **the answer is not transferable to a different assumption set.**

Then answer the question the user actually has — *may I stop thinking about this?*

```python
report.analysis_is_complete    # no further computation can improve this
report.assumptions_to_confirm  # facts to check; wrong ones change the decision
report.execution_note          # the above, in a sentence you can say out loud
```

`analysis_is_complete` means the remaining risk is **factual, not analytical**: more
deliberation cannot help, only checking the world can. Telling a user they may stop analyzing
is part of the deliverable, not a courtesy.

---

## Weight (权重) and the overturn test

**Weight is the magnitude of causal control a factor exerts over the outcome, given a concrete
goal, a specific time scale, and defined objects of comparison.** There is no standard answer
for weight; it depends entirely on the objective function (目标函数).

Two consequences shape the whole of Stage 1.

**Weight is a product of the dialogue, not a library computation.** The AI cannot rank factors
by importance in the abstract, because importance is not a property of a factor — it is a
property of a factor *relative to a stated goal*. So the AI **coaches** the user toward
articulating the goal, and the **user decides** it. `classify_job` reads contract fields and
never user prose for precisely this reason: the moment the AI picks the objective function,
every weight downstream is the AI's opinion wearing the user's name.

The three prerequisites (`WEIGHT_PREREQUISITES`) are therefore not screenable:

| Prerequisite | Contract fields |
|---|---|
| 给定目标 | `payoff`, `attributes`, `scaling_constants`, `risk_attitude` |
| 给定时间尺度 | `horizon`, `gamma`, `n`, `n_max`, `stop_prob_per_step` |
| 给定比较对象 | `alternatives`, `states`, `actions` |

`overturn_test` raises `ContractIncomplete` before these are stated, rather than inventing a
baseline. Without them no factor has a weight yet.

**The test for weight is overturn capacity.** Do not ask "what other details have I not
considered?" — details are infinite and the question never terminates. Ask the one question
that does:

> Is the presence or absence of this factor sufficient to overturn my current conclusion?

If it is not sufficient, it is a high-order perturbation — a small quantity — so throw it out of
the dominant equation immediately.

```python
plan = elicitation_plan(contract)
plan["required"]      # no conclusion exists yet; ask these
plan["load_bearing"]  # passed the overturn test
plan["droppable"]     # failed it — do not ask
```

`overturn_test` answers by *recomputing*, not by heuristic: it re-dispatches the contract under
each corpus-calibrated alternative and compares decisions. A refusal counts as an overturn — if
setting a factor makes the problem uncalibrated, the factor is emphatically load-bearing.

This is why the library can screen honestly instead of guessing. The same factor goes both ways:

| Pool size | exact | asymptotic | Overturn? | Verdict |
|---|---|---|---|---|
| n = 50 | 19 | 18 | **yes** | load-bearing — worth a question |
| n = 45 | 17 | 17 | no | 舍去项 — throw it out |
| n = 102 | 38 | 38 | no | 舍去项 — throw it out |

"Should I use the exact computation or the famous 37% rule?" is a real question at n=50 and a
waste of the user's attention at n=45. No fixed list of "important factors" survives between
conversations; each must be screened against the goal actually stated.

This is also the answer to 大局观的另一半 — knowing when to stop looking. `plan["required"] == []`
with an empty `load_bearing` means there is nothing left worth asking, which is a computed
result rather than a judgement call.

## The zero-order expansion (零阶展开)

Every report carries `report.perturbation` — the answer as a labelled series rather than a
single number, which is what makes the perturbation structure visible instead of implicit.

| Order | 中文 | Meaning |
|---|---|---|
| `ORDER_ZERO` | 零阶 | The trunk. What the dominant terms alone give. |
| `ORDER_FIRST` | 一阶修正 | Refines the trunk. **Cannot overturn it.** |
| `ORDER_OVERTURN` | 翻盘 | Not a correction — a *different* trunk. |
| `ORDER_DROPPED` | 舍去项 | Thrown away by 主导平衡 as having no causal control. |
| `ORDER_HARD` | 硬约束 | No trunk exists. A veto, never a small quantity. |

**The classification is structural, never a magnitude threshold.** A term is a *correction*
when it refines the same calibrated model, and an *overturn* when it moves the problem to a
different row of the corpus decision table. This matters because the two are independent — for
a pool of 50:

| Order | Term | Value | Δ | Citation |
|---|---|---|---|---|
| 零阶 | asymptotic 1/e — the 37% rule | 18 | — | c01 §5 |
| 一阶修正 | exact finite-*n* argmax | 19 | +6% | c01 §4.1 |
| 翻盘 | recall allowed at 50% | 30 | +67% | c01 §7 |
| 翻盘 | rejection risk at 50% | 12 | −33% | c01 §7 |
| 硬约束 | payoff diverges | no rule exists | — | c01 §8 |

The +6% term is a correction; the −33% term is an overturn. Sorting by size would invert both.
Recall and rejection are not 修正项 at all: each is calibrated for a different assumption set,
so each *is* a trunk. That is also why the corpus has no joint row for them — they move the
boundary in opposite directions, and there is no series in which one is a small perturbation of
the other.

Each engine's trunk is a real quantity from the corpus, not a label:

- **Engine A** — the closed-form constant for the elicited row (c01 §5 / §7). The one genuine
  correction available is exact finite-*n* vs the asymptotic limit (c01 §4.1).
- **Engine B** — the additive score. c02 §5.3 states outright that additive is the \(k=0\)
  special case of the multiplicative form, so \(k\) *is* the perturbation parameter and the
  interaction term is the correction.
- **Engine C** — the myopic action at \(\gamma = 0\). The Bellman equation is itself a series in
  \(\gamma\); the discounted future terms are the corrections, and residuals shrinking by
  \(\le \gamma\) per sweep (INV-4) is exactly why the series converges and later terms cannot
  overturn the trunk.

This also gives 硬约束 its precise place. 「微扰级数不一定收敛」is not a metaphor here: when the
expected payoff at the best stopping point diverges, there is no zero-order term to correct, and
c01 §8 says so formally. The veto is the framework's own boundary, not an exception bolted on.

## What this design forbids

Each of these is enforced in code and covered by a test, not merely aspired to.

| Forbidden | Enforcement |
|---|---|
| Answering before the contract is complete | `ContractIncomplete`, `missing_fields` |
| Inferring a field the user did not state | `is None` discipline; `classify_job` reads fields only |
| Reusing a constant outside its calibrated assumption set | INV-1 via `CALIBRATIONS` |
| Additive/multiplicative form without covered independence | `IndependenceNotVerified` (every proper subset) |
| Treating a scaling constant as a free-floating "importance weight" | INV-5, ranges attached |
| Answering a diverging-payoff game | `NoOptimalStoppingRuleExists` |
| Applying Bellman methods to a non-Markov process | `NonMarkovProcess` |
| Inventing a constant the corpus does not cover | `UnclassifiedVariant` |
| Returning a decision whose audit failed | `AuditFailure` |
| Citing a cluster section for a number the corpus doesn't support | `tests/test_corpus.py` |
| Any I/O or prompting inside `src/` | `tests/test_api.py::test_no_input_calls_in_src` |
