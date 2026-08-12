# Dominant-Circuit

[![Python application](https://github.com/ariel-lee-1023/dominant-circuit/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/ariel-lee-1023/dominant-circuit/actions/workflows/python-app.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Think in models, then compute only what the model licenses.**

Two layers, one discipline. [`stage0/`](stage0/SKILL.md) is a prose skill that turns an unshaped
situation into an explicit model and tells you where to look. `src/dominant_circuit/` is a **pure,
non-interactive library** — no `input()`, no network, no hidden state — that takes the resulting
contract and returns a constant, or refuses. The host AI owns every word spoken to the human; the
package owns the physics.

MIT © 2026 Ariel Lee. [See LICENSE](LICENSE).
This license covers the original text in this repository. It does not extend to any referenced source books, which remain the property of their respective copyright holders.

---

## The methodology

Data does not announce what caused it. A person staring at a falling number cannot see, in the
number, which of a dozen mechanisms produced it — and no amount of further staring will tell them.
Judea Pearl's formulation is the blunt one: **no causes in, no causes out.** A causal conclusion is
never a property of the data alone; it is a property of the data *plus* a model you brought with you.

Two consequences run through the whole design.

**You are always already using a model.** Choosing what to measure is choosing a boundary, and a
boundary is a modelling decision, not a discovered fact (Meadows). Choosing a model class fixes
which answers are even expressible — an equilibrium model cannot return "it cycles forever," so
picking one has quietly answered a question nobody asked (Page). The realistic choice is never
*model or no model*. It is **deliberate model or inherited one**.

**So the model gets written down first, and out loud.** Stage 0 installs one and prints what it
commits to, what it forbids, what would overturn it, and which rival models were live. Then, and
only then, the library computes — and it computes only what that model makes identifiable.

What this buys you: an answer you can audit. Every number arrives welded to the assumption set it
was derived under, and every refusal names which assumption is missing rather than degrading into a
plausible-looking figure.

## What it refuses to do

Refusal is the product, not a failure mode. The library says *no* as readily as it says a number:

- **No silent 37%.** Every constant is locked to the assumption set it was derived under. Ask
  for one outside its calibrated row and you get `UnclassifiedVariant`, not a plausible figure.
- **No additive utility without verified independence.** And "verified" means every proper
  nonempty subset of attributes checked against its complement (c02 §7.3) — not one recorded
  pair.
- **No answer to a diverging-payoff game.** `NoOptimalStoppingRuleExists` is a *correct*
  outcome, not a failure.
- **No causal claim from observational data alone.** If the user's own graph makes the effect
  unidentifiable, Stage 0 says which measurement would fix it — it does not average the data
  harder.
- **No number without its citation and its assumptions.** Answers are non-transferable to a
  different assumption set, and the report says so.
- **No `input()`.** The library never asks anything. All conversation belongs to the host.

An assumption the user never made is the failure this system exists to prevent.

---

## Stage 0 — install a model before you look

Stages 1–5 assume the problem has already been reduced to job / horizon / information / payoff.
Reducing it is a different job, and it needs the **opposite default**.

Stages 1–5 refuse because a user who asked for a number and got a wrong one will act on it. Stage 0's
user asked for *a direction to look*, and arrives with no declared boundary and no named structure —
that is why they came. Refusing there hands them back the unexamined model they walked in with. So
Stage 0 commits, and makes the commitment inspectable.

It works through three books in a fixed order, because each answers a question the next one depends
on:

| Source | Question it settles |
|---|---|
| Meadows, *Thinking in Systems* | What are the nouns? Stocks, flows, feedback loops, delays — and where is the boundary? |
| Pearl & Mackenzie, *The Book of Why* | What is licensed? Which claims does this graph support, and what is simply not identifiable? |
| Page, *The Model Thinker* | What shape can the answer take? Equilibrium, cycle, randomness, or complexity? |

**Six required output fields**, and the second may never be omitted: starting model · **observation
instruction** · commitments · prohibitions · overturn conditions · rival models.

**Twelve verdicts, deliberately unequal.** Six are true refusals of a specific over-reaching claim
(`NotIdentifiable`, `ConditioningOnCollider`, `UnobservedConfounder`, …). Three are *forks* that may
never terminate the stage — a `BoundaryFork` lays out candidate boundaries and prices each, because
the user has to choose one, not be handed one. Three are findings that terminate only with a
resolving measurement attached: "undetermined, and here is what would determine it."

Stage 0 emits **no numbers at all**. It fills only the four classifying contract fields and names
every numeric field as something the host must still elicit. See [stage0/SKILL.md](stage0/SKILL.md);
its drift guards are in `tests/test_stage0.py`.

## The five stages, and who owns them

The host AI owns the conversation at both ends; the library owns the physics in the middle.

| Stage | Owner | What happens | Entry point |
|---|---|---|---|
| **0. Structure** | **Host** | Install an explicit model and say where to look. Hand off four classifying fields, or refuse a specific claim. | [stage0/SKILL.md](stage0/SKILL.md) |
| **1. Elicitation** | **Host** | Refuse to compute until the boundary conditions are locked. Horizon, information type, recall/rejection. | `next_question`, `missing_fields`, `classify_job` |
| **2. Verification** | Library | Reject premises that break the mathematics before any equation loads. | `verify_preconditions`, `independence_questions`, `run_flip_test` |
| **3. Computation** | Library | Route the validated contract to the one formula its assumption set selects. | `dispatch`, `CALIBRATIONS` |
| **4. Auditing** | Library | Prove the work before the human sees it. Failure raises; it is never buried in a returned report. | `run_validation_invariants`, `AuditFailure` |
| **5. Reporting** | **Host** | Deliver the action, the formula, the assumptions that make it valid — and say when to stop analyzing. | `OutputReport.action`, `.execution_note` |

The handoff from 0 to 1 is all-or-nothing: `job`, `horizon`, `information`, and `payoff` must **all**
classify. If one does not, the case stops at Stage 0 with its six fields and a verdict, because
asking for numbers while the shape is still undetermined is precisely the error this repository
exists to catch.

`AuditFailure` carries `.invariant_ids` and `.fields`, so Stage 4 loops back to Stage 1 on the
*specific* contradictory input rather than restarting the interrogation.

See [SKILL.md](SKILL.md) for the host protocol and a worked interaction transcript, and
[DESIGN.md](DESIGN.md) for the interaction model in full — including why each refusal is a
designed output rather than a failure. [AGENTS.md](AGENTS.md) indexes every governing document
and its status.

---

## Install

```bash
pip install -e ".[dev]"
```

## Quick start

```python
from dominant_circuit import (
    dispatch, InputContract, Job, Horizon, Information, Payoff,
    AttributeRange, record_independence, independence_questions,
)

# Engine A — classical secretary, exact finite-n
report = dispatch(Job.STOPPING, InputContract(
    job=Job.STOPPING,
    horizon=Horizon.FIXED_KNOWN,
    n=100,
    information=Information.ORDINAL,
    payoff=Payoff.BEST_OR_NOTHING,
    payoff_diverges=False,   # must be explicit; never defaulted
    exact_finite_n=True,
))
print(report.numeric["r_star"])   # 38, not 37 — the exact argmax, not the asymptotic limit
print(report.action)              # the decision as an instruction you can carry out
print(report.execution_note)      # whether you may stop analyzing and act

# Engine B — additive MAUT. Independence must be COVERED, not merely asserted:
# every proper nonempty subset against its complement (c02 §7.3).
contract = InputContract(
    job=Job.MULTIOBJECTIVE,
    attributes=[
        AttributeRange("salary", 40, 100),
        AttributeRange("commute", 60, 10, monotonic_increasing=False),
    ],
    scaling_constants={"salary": 0.65, "commute": 0.35},
    independence_assumptions=[],      # [] = asked, nothing verified yet
    alternatives=[
        {"name": "A", "salary": 80, "commute": 20},
        {"name": "B", "salary": 60, "commute": 15},
    ],
)
# independence_questions() tells the host exactly what to ask.
for subset, complement, question in independence_questions(contract):
    ...  # put `question` to the user
    contract.independence_assumptions.append(
        record_independence(subset, complement, contract.independence_kind,
                            verified=True, evidence="flip test / Question II")
    )
report = dispatch(Job.MULTIOBJECTIVE, contract)

# Engine C — MDP value iteration
report = dispatch(Job.SEQUENTIAL, InputContract(
    job=Job.SEQUENTIAL,
    horizon=Horizon.INFINITE_DISCOUNTED,
    gamma=0.9,
    markov_verified=True,    # must be explicit; non-Markov raises
    states=["s0", "s1"],
    actions=["stay", "go"],
    reward={("s0", "go"): 1.0, ("s1", "stay"): 2.0, ("s0", "stay"): 0.0, ("s1", "go"): 0.0},
    transition={
        ("s0", "stay"): {"s0": 1.0}, ("s0", "go"): {"s1": 1.0},
        ("s1", "stay"): {"s1": 1.0}, ("s1", "go"): {"s0": 1.0},
    },
))
```

Run `python main.py` for five non-interactive demos, including the Stage 1 elicitation loop
and the Stage 2 independence protocol.

### What a refusal looks like

```python
from dominant_circuit import dispatch, InputContract, Job, Horizon, Information, Payoff
from dominant_circuit import NoOptimalStoppingRuleExists

try:
    dispatch(Job.STOPPING, InputContract(
        job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=10,
        information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
        payoff_diverges=True,          # triple-or-nothing with full re-wagering
    ))
except NoOptimalStoppingRuleExists as e:
    print(e.remedy)   # -> switch to a bankroll-fraction framework (Kelly)
```

This is the library working correctly. There is no cutoff to report.

---

## Layout

```
stage0/                   # Stage 0 prose skill + its three references (not installed)
src/dominant_circuit/
├── core/          # contract, errors, elicit, verify, audit, dispatch, report
└── engines/
    ├── stopping.py       # Engine A (c01)
    ├── multiobjective.py # Engine B (c02)
    └── sequential.py     # Engine C (c03)
references/clusters/      # authoritative corpus — never edited to fit the code
tests/                    # golden numeric oracles + corpus/API drift guards
DESIGN.md                 # the five-stage interaction model
SPEC.md                   # implementation spec v1.0 (historical)
docs/SPEC-2-PUNCHLIST.md  # punch list v2.0, T0-T9 — closed (historical)
main.py                   # five non-interactive demos
```

## Tests

```bash
pytest
```

180 tests, 93% coverage, with an 80% floor enforced in `pyproject.toml`. Every push and pull
request to `main` runs lint plus the full suite — the badge above is that workflow.

The suite includes guards that exist because of specific past failures:
`tests/test_corpus.py` enforces cluster size floors and that every `citation=` string
resolves to a real numbered section; `tests/test_api_surface.py` stops the public API
shrinking silently; `tests/test_product_intent.py` pins the four claims the product exists
to make good on; `tests/test_stage0.py` checks that every `pearl §2.7`-style citation resolves and
that acceptance-probe wording never leaks into the references it is meant to test. See
**Change discipline** in [AGENTS.md](AGENTS.md).

## Corpus

Computable formula clusters, cited by the engines:

- `references/clusters/c01-optimal-stopping.md`
- `references/clusters/c02-multiple-objectives.md`
- `references/clusters/c03-sequential-decisions.md`

Structural-judgment references, cited by Stage 0 — decision criteria and named results, not
formulas to compute with:

- `stage0/references/reference-meadows-thinking-in-systems.md`
- `stage0/references/reference-pearl-book-of-why.md`
- `stage0/references/reference-page-model-thinker.md`

Host AI (via [SKILL.md](SKILL.md)) must search the corpus before answering; matching content
is authoritative. If the corpus does not cover the elicited assumption set, the correct
answer is to say so — never to supply a constant from memory.
