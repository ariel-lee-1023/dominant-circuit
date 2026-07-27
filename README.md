# Dominant-Circuit

**A pure, non-interactive decision-mechanics library.**  
Host AI owns conversation. This package is the physics engine.

MIT © 2026 Ariel Lee. [See LICENSE](LICENSE).  
This license covers the original text in this repository. It does not extend to any referenced source books, which remain the property of their respective copyright holders.

---

## What it does

Five-stage pipeline enforced in code:

1. **Elicit** — `InputContract` completeness (`missing_fields` / `ContractIncomplete`)
2. **Verify** — hard preconditions (`IndependenceNotVerified`, `NoOptimalStoppingRuleExists`, `NonMarkovProcess`)
3. **Compute** — route to one of three engines
4. **Audit** — normalization, Bellman residual contraction, overdetermination
5. **Report** — six-field `OutputReport` (decision, formula, citation, numeric, assumptions, sensitivity, audit)

No `input()`. No silent 37%. No additive utility without a recorded flip-test.

---

## Install

```bash
pip install -e ".[dev]"
```

## Quick start

```python
from dominant_circuit import (
    dispatch, InputContract, Job, Horizon, Information, Payoff,
    AttributeRange, IndependenceTest,
)

# Engine A — classical secretary, exact finite-n
report = dispatch(Job.STOPPING, InputContract(
    job=Job.STOPPING,
    horizon=Horizon.FIXED_KNOWN,
    n=100,
    information=Information.ORDINAL,
    payoff=Payoff.BEST_OR_NOTHING,
    payoff_diverges=False,   # must be explicit
    exact_finite_n=True,
))
print(report.numeric["r_star"])  # 38, not 37

# Engine B — additive MAUT (independence verified)
report = dispatch(Job.MULTIOBJECTIVE, InputContract(
    job=Job.MULTIOBJECTIVE,
    attributes=[
        AttributeRange("salary", 40, 100),
        AttributeRange("commute", 60, 10, monotonic_increasing=False),
    ],
    scaling_constants={"salary": 0.65, "commute": 0.35},
    independence_tests=[
        IndependenceTest(("salary", "commute"), "flip_test", True),
        IndependenceTest(("salary", "commute"), "question_ii", True),
    ],
    alternatives=[
        {"name": "A", "salary": 80, "commute": 20},
        {"name": "B", "salary": 60, "commute": 15},
    ],
))

# Engine C — MDP value iteration
report = dispatch(Job.SEQUENTIAL, InputContract(
    job=Job.SEQUENTIAL,
    horizon=Horizon.INFINITE_DISCOUNTED,
    gamma=0.9,
    markov_verified=True,
    states=["s0", "s1"],
    actions=["stay", "go"],
    reward={("s0", "go"): 1.0, ("s1", "stay"): 2.0, ("s0", "stay"): 0.0, ("s1", "go"): 0.0},
    transition={
        ("s0", "stay"): {"s0": 1.0}, ("s0", "go"): {"s1": 1.0},
        ("s1", "stay"): {"s1": 1.0}, ("s1", "go"): {"s0": 1.0},
    },
))
```

---

## Layout

```
src/dominant_circuit/
├── core/          # contract, errors, elicit, verify, audit, dispatch, report
└── engines/
    ├── stopping.py       # Engine A (c01)
    ├── multiobjective.py # Engine B (c02)
    └── sequential.py     # Engine C (c03)
references/clusters/      # authoritative corpus
tests/                    # golden numeric oracles
```

## Tests

```bash
pytest
```

## Corpus

- `references/clusters/c01-optimal-stopping.md`
- `references/clusters/c02-multiple-objectives.md`
- `references/clusters/c03-sequential-decisions.md`

Host AI (via `SKILL.md`) must search the corpus before answering; matching content is authoritative.
