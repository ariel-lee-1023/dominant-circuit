# Dominant-Circuit

**A pure, non-interactive decision-mechanics library.**
Host AI owns conversation. This package is the physics engine.

MIT © 2026 Ariel Lee. [See LICENSE](LICENSE).
This license covers the original text in this repository. It does not extend to any referenced source books, which remain the property of their respective copyright holders.

---

## What this is for

When a person brings a decision to an AI paired with this library, they are not chatting.
They are plugging a problem into a centrifuge. The design purpose is to **strip the vibes off
a dilemma and show the constants underneath** — and to refuse, loudly, when the problem as
stated has no mathematical answer.

That means the library is built to say *no* as readily as it says a number:

- **No silent 37%.** Every constant is locked to the assumption set it was derived under. Ask
  for one outside its calibrated row and you get `UnclassifiedVariant`, not a plausible figure.
- **No additive utility without verified independence.** And "verified" means every proper
  nonempty subset of attributes checked against its complement (c02 §7.3) — not one recorded
  pair.
- **No answer to a diverging-payoff game.** `NoOptimalStoppingRuleExists` is a *correct*
  outcome, not a failure.
- **No number without its citation and its assumptions.** Answers are non-transferable to a
  different assumption set, and the report says so.
- **No `input()`.** The library never asks anything. All conversation belongs to the host.

An assumption the user never made is the failure this system exists to prevent.

## The five stages, and who owns them

The host AI owns the conversation at both ends; the library owns the physics in the middle.

| Stage | Owner | What happens | Entry point |
|---|---|---|---|
| **1. Elicitation** | **Host** | Refuse to compute until the boundary conditions are locked. Horizon, information type, recall/rejection. | `next_question`, `missing_fields`, `classify_job` |
| **2. Verification** | Library | Reject premises that break the mathematics before any equation loads. | `verify_preconditions`, `independence_questions`, `run_flip_test` |
| **3. Computation** | Library | Route the validated contract to the one formula its assumption set selects. | `dispatch`, `CALIBRATIONS` |
| **4. Auditing** | Library | Prove the work before the human sees it. Failure raises; it is never buried in a returned report. | `run_validation_invariants`, `AuditFailure` |
| **5. Reporting** | **Host** | Deliver the action, the formula, the assumptions that make it valid — and say when to stop analyzing. | `OutputReport.action`, `.execution_note` |

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
src/dominant_circuit/
├── core/          # contract, errors, elicit, verify, audit, dispatch, report
└── engines/
    ├── stopping.py       # Engine A (c01)
    ├── multiobjective.py # Engine B (c02)
    └── sequential.py     # Engine C (c03)
references/clusters/      # authoritative corpus — never edited to fit the code
tests/                    # golden numeric oracles + corpus/API drift guards
DESIGN.md                 # the five-stage interaction model
SPEC.md, SPEC-2-PUNCHLIST.md   # implementation spec + punch list (historical)
main.py                   # five non-interactive demos
```

## Tests

```bash
pytest
```

The suite includes guards that exist because of specific past failures:
`tests/test_corpus.py` enforces cluster size floors and that every `citation=` string
resolves to a real numbered section; `tests/test_api_surface.py` stops the public API
shrinking silently; `tests/test_product_intent.py` pins the four claims the product exists
to make good on. See **Change discipline** in [AGENTS.md](AGENTS.md).

## Corpus

- `references/clusters/c01-optimal-stopping.md`
- `references/clusters/c02-multiple-objectives.md`
- `references/clusters/c03-sequential-decisions.md`

Host AI (via [SKILL.md](SKILL.md)) must search the corpus before answering; matching content
is authoritative. If the corpus does not cover the elicited assumption set, the correct
answer is to say so — never to supply a constant from memory.
