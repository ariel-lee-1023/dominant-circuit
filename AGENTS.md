# AGENTS.md — Dominant-Circuit Knowledge Base

This repository is the **executable knowledge base + physics engines** for the Dominant-Circuit decision-mechanics router.

## Pairing Rule (mandatory for host AIs)

1. The companion skill `dominant-circuit` (see `SKILL.md`) is the analytical router / perspective.
2. This repository supplies the authoritative zero-order formulas, decision tables, and runnable Python engines.
3. Before answering any decision-structure query, the host AI **must** consult the matching cluster under `references/clusters/` and, when computation is required, invoke the corresponding engine via the `dominant_circuit` package.
4. Matching content is authoritative. If no matching content exists, the host must stay in character and must **not** invent formulas outside the zero-order set documented here.
5. Never silently substitute the classical 37 % assumption set. The Input Contract must be fully elicited.
6. The `dominant_circuit` package is a pure, non-interactive library. It performs no I/O and asks no questions. All conversation is the host's responsibility.
7. Install with `pip install -e .` from the repository root before use. If the import fails, the host must say the engine is unavailable rather than computing in prose.
8. If a cluster file required by the query is missing or does not cover the elicited assumption set, refuse the query and say so. Never answer from `SKILL.md`'s inlined formulas while citing a cluster section — that produces a real-looking citation for a number the corpus does not support.

## Governing documents

Read in this order. All are committed; a fresh clone is self-contained.

| Document | What it is | Status |
|---|---|---|
| [DESIGN.md](DESIGN.md) | The five-stage interaction model — what the product is *for*, and why every refusal is a designed output rather than an error path. | **Current.** Authoritative on intent. |
| [SKILL.md](SKILL.md) | The file a host AI loads. Host protocol, elicitation questions, worked transcript. | **Current.** Authoritative on host behaviour. |
| AGENTS.md | This file. Pairing rules, enforced invariants, change discipline. | **Current.** |
| [README.md](README.md) | Front door: purpose, install, quick start. | **Current.** |
| [SPEC.md](SPEC.md) | Implementation specification v1.0 — module layout (§3), data contracts (§4), the D-01…D-29 defect register, acceptance criteria (§15). | **Historical, partly superseded.** Authoritative for the numbered requirements other documents cite. Its §3 layout still holds; some test filenames in it were later reorganised. |
| [SPEC-2-PUNCHLIST.md](SPEC-2-PUNCHLIST.md) | Punch list v2.0 — tasks T0–T9, implemented in PR #1. | **Historical.** Supersedes SPEC.md where they conflict. |

Where DESIGN.md and the SPEC documents disagree about *mechanics*, the SPEC documents win.
Where a reader wants to know *why* a refusal is correct behaviour, DESIGN.md wins.

**`solvers.py` does not exist and must not be reintroduced.** It was the pre-rewrite Stage 3
module (baseline `a66504d`); SPEC.md logs defects D-12 and D-13 against it and closes them by
splitting it into `core/dispatch.py` (routing) and the `engines/` package (solving). Older text
naming `solvers.py` means those two together. See DESIGN.md § Stage 3.

## Directory Map

Generated from `find . -not -path './.git/*' -type f | sort`.

```
.github/workflows/python-app.yml  # CI: lint, install package, pytest + coverage gate
.gitignore
AGENTS.md                         # This file — host-AI pairing rules
DESIGN.md                         # The five-stage interaction model (design intent)
LICENSE
NOTICE.md                         # Source attribution for the corpus
README.md
SKILL.md                          # Router skill (elicitation + dispatch rules)
SPEC.md                           # Implementation spec v1.0 (historical, cited by §number)
SPEC-2-PUNCHLIST.md               # Punch list v2.0, tasks T0-T9 (historical)
main.py                           # Non-interactive demo of the three engines
pyproject.toml
references/clusters/
  c01-optimal-stopping.md         # Engine A source of truth
  c02-multiple-objectives.md      # Engine B source of truth
  c03-sequential-decisions.md     # Engine C source of truth
src/dominant_circuit/
  __init__.py                     # Public API surface (__all__)
  py.typed
  core/
    __init__.py
    contract.py                   # InputContract, enums, AttributeRange, independence records
    elicit.py                     # Stage 1: QUESTION_BANK, missing_fields, next_question
    verify.py                     # Stage 2: hard precondition blockers
    dispatch.py                   # Stage 3: verify -> compute -> audit -> report
    audit.py                      # Stage 4: validation invariants INV-1..INV-7
    report.py                     # OutputReport, AuditResult, InvariantResult
    errors.py                     # Typed error taxonomy with .remedy / .field
  engines/
    __init__.py
    stopping.py                   # Engine A (c01)
    multiobjective.py             # Engine B (c02)
    sequential.py                 # Engine C (c03)
tests/
  test_api.py
  test_api_surface.py             # public __all__ may not shrink silently
  test_audit_and_report.py        # INV-1..INV-7 and Output Contract rendering
  test_corpus.py                  # corpus/code drift guards (sizes, sections, citations)
  test_interaction_stages.py      # the five-stage interaction model, as a host drives it
  test_multiobjective.py
  test_product_intent.py          # the four claims the product exists to make good on
  test_sequential.py
  test_stopping.py
```

## Engineering Invariants

What is actually enforced in code, by invariant ID:

- **INV-1 (assumption-set match)** — enforced. `engines/stopping.py::check_assumption_set_match`
  compares the elicited assumption tuple against the `Calibration` record of the constant
  actually dispatched. A mismatch on any pinned field fails the audit; it is not a literal.
- **INV-2 (belief normalization)** — enforced, computed from the posterior in `engines/sequential.py`.
- **INV-3 (independence verified + form agreement)** — enforced. Registry coverage is checked by
  `mutual_independence_holds` (c02 §7.3), and the recorded flip test's implied form must agree
  with the form implied by `sum(k_i)`.
- **INV-4 (Bellman residual monotonicity)** — enforced, computed from the residual history.
- **INV-5 (range-fixed weights)** — enforced twice, deliberately: `core/verify.py` blocks before
  computing, `check_range_fixed_weights` records the result in the report.
- **INV-6 (finite expectation)** — enforced. `payoff_diverges=True` raises
  `NoOptimalStoppingRuleExists` in Stage 2, before any formula runs.
- **INV-7 (overdetermination)** — **conditional, not blocking.** It is reported when the
  elicitation supplies enough structure to count trade-off equations against free parameters,
  and is otherwise omitted. A passing report does not prove the elicitation was overdetermined.

Additionally:

- Every returned `OutputReport` carries the full assumption list and audit results.
- Scaling constants are never treated as free-floating “importance weights”; ranges are attached.

## Change discipline

Deleting corpus content or public API symbols requires an explicit line in the commit body
beginning `REMOVES:`. A commit whose stated purpose is a fix must not also delete unrelated
content.

Two tests enforce this mechanically, and both are meant to be *updated in the same commit*
as any deliberate removal, never silenced:

- `tests/test_corpus.py::test_cluster_minimum_sizes` — line floors on the three cluster files,
  set ~10% below their restored sizes. This is what commit `a2d99aa` would have tripped when
  it deleted 223 lines of `c01` under the title "Correct c01 §10 parking formula".
- `tests/test_api_surface.py::test_public_api_surface_is_stable` — `EXPECTED_EXPORTS` is the
  public `__all__` as of T8. Removing an export fails the build until the removal is written
  down.

## License & Attribution

MIT © 2026 Ariel Lee. [See LICENSE](LICENSE).

This license covers the original text in this repository. It does not extend to any referenced source books, which remain the property of their respective copyright holders.

See [NOTICE.md](NOTICE.md) for full source attribution.
