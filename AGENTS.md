# AGENTS.md — Dominant-Circuit Knowledge Base

This repository is the **executable knowledge base + physics engines** for the Dominant-Circuit decision-mechanics router.

## Pairing Rule (mandatory for host AIs)

1. The companion skill `dominant-circuit` (see `SKILL.md`) is the analytical router / perspective.
2. This repository supplies the authoritative zero-order formulas, decision tables, and runnable Python engines.
3. Before answering any decision-structure query, the host AI **must** consult the matching cluster under `references/clusters/` and, when computation is required, invoke the corresponding engine via the `dominant_circuit` package.
4. Matching content is authoritative. If no matching content exists, the host must stay in character and must **not** invent formulas outside the zero-order set documented here.
5. Never silently substitute the classical 37 % assumption set. The Input Contract must be fully elicited.

## Directory Map

```
SKILL.md                          # Router skill (elicitation + dispatch rules)
references/clusters/
  c01-optimal-stopping.md         # Engine A source of truth
  c02-multiple-objectives.md      # Engine B source of truth
  c03-sequential-decisions.md     # Engine C source of truth
src/dominant_circuit/
  core/                           # Contract, verify, audit, dispatch
  engines/                        # The three physics engines
tests/                            # Smoke tests for every engine
```

## Engineering Invariants

- All hard preconditions (diverging payoff, independence, Markov, range-fixed weights) are enforced in code before any formula runs.
- Every returned `OutputReport` carries the full assumption list and audit results.
- Scaling constants are never treated as free-floating “importance weights”; ranges are attached.

## License & Attribution

MIT © 2026 Ariel Lee. [See LICENSE](LICENSE).

This license covers the original text in this repository. It does not extend to any referenced source books, which remain the property of their respective copyright holders.

See [NOTICE.md](NOTICE.md) for full source attribution.
