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
