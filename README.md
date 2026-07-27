# Dominant-Circuit Engine

**Master decision-mechanics router** for choosing when to stop a search, how to trade off multiple objectives under certainty or uncertainty, and how to select or time actions in sequential/uncertain environments.

This is a rigid, zero-order mathematical pipeline. It is **not** a conversational chatbot. It forces clarification of zero-order principles and computes the mathematically optimal action under strict physical and probabilistic constraints.

## Architectural Stages

1. **Elicit** — Front-end state machine that interrogates the user until the Input Contract is complete.
2. **Verify** — Validation layer that blocks computation if physical or mathematical laws are violated.
3. **Compute** — Switchboard that routes valid parameters to one of three physics engines.
4. **Audit & Report** — Final check of mathematical invariants before any answer is shown.

## The Three Physics Engines

| Engine | Cluster | Trigger |
|--------|---------|---------|
| A. Optimal Stopping | `references/clusters/c01-optimal-stopping.md` | when to stop looking / secretary / threshold / cost-of-search |
| B. Multiple Objectives | `references/clusters/c02-multiple-objectives.md` | multiattribute utility / scaling constants / preferential independence |
| C. Sequential Decisions | `references/clusters/c03-sequential-decisions.md` | MDP / POMDP / Bellman / value iteration / belief update |

## Hard Precondition Blockers

- **Diverging Payoff** — abort if expected reward at the best stopping point is infinite.
- **Independence** — additive/multiplicative forms forbidden unless flip-test (or equivalent) has been verified.
- **Markov** — sequential models require the next state to depend only on current state + action.

## Input Contract (must be fully elicited)

1. Horizon (fixed known \(n\), distributional, open-ended/stochastic)
2. Feasible alternatives / states / actions / candidate stream
3. Objective hierarchy + explicit [worst, best] ranges per attribute
4. Preferential / utility independence assumptions (verified, never assumed)
5. Uncertainty model / prior / observation model
6. Search costs / recall / rejection probabilities
7. Risk attitude
8. Computational budget / tolerance

## Output Contract

Every answer reports:

1. Chosen action / stop decision / threshold
2. Exact zero-order formula used (with cluster + section citation)
3. Belief / value / threshold numeric
4. Full list of locked assumptions
5. Sensitivity to the most contested assumptions
6. Any audit failures with residuals

## Installation

```bash
pip install -e .
```

## Usage (Python API)

```python
from dominant_circuit import dispatch, InputContract

contract = InputContract(...)  # fully filled via Socratic loop
result = dispatch(job="stopping", contract=contract)
print(result.decision, result.formula, result.assumptions, result.audit)
```

## Skill Pairing

This repository is the **knowledge base + executable engines**.  
The companion skill `dominant-circuit` (SKILL.md) is the analytical router that host AIs must follow: search this corpus first, stay in character, never invent formulas outside the zero-order set.

## License

MIT © 2026 Ariel Lee. [See LICENSE](LICENSE).

This license covers the original text in this repository. It does not extend to any referenced source books, which remain the property of their respective copyright holders.

See also [NOTICE.md](NOTICE.md) for full attribution of the source mathematical literature.

## Anti-Cargo-Cult Rules (enforced in code)

- Never emit “37 %” without the classical assumption set attached.
- Never treat \(k_i\) as an “importance weight” without its assessed range.
- Never assume additive separability; require the flip test.
- Never apply a stopping rule to a diverging-expectation game.
- Never skip dominance screening or over-determination checks.
