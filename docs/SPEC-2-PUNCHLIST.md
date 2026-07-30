# Dominant-Circuit — Punch List Specification v2.0

**For:** Claude Code
**Repository:** https://github.com/ariel-lee-1023/dominant-circuit
**Baseline audited:** commit `f66506c` ("Create python-app.yml"), clusters manually restored by the owner
**Predecessor:** `SPEC.md` v1.0 — still authoritative for anything not superseded here
**Date:** 2026-07-27

---

## 0. Instructions for the implementing agent

Read this section fully before touching any file.

**Working rules**

1. Work tasks in order, **T0 → T9**. Each task is independently committable. Do not batch unrelated tasks into one commit.
2. After every task, run `python -m pytest -q` from the repository root. The suite must be green before you start the next task. If a task legitimately requires changing an existing test's expectation, say so explicitly in the commit message and explain why the old expectation was wrong.
3. **Do not modify any file under `references/clusters/` except for the single formula edit specified in T0.** The three cluster files were manually restored by the repository owner and are the authoritative mathematical corpus. Changing them changes what the product is permitted to say. If you believe a cluster is wrong, stop and report rather than editing.
4. **Do not delete content to make a test pass.** A prior commit (`a2d99aa`) removed 223 lines of `c01` while claiming to fix a formula. That regression is why T9 exists. Deletions from the corpus or from the public API must be called out explicitly in the commit body.
5. The library is **pure and non-interactive**. No `input()`, no network calls, no printing from within `src/`. The host AI is the conversational front end.
6. Never invent a formula. Every computed constant must trace to a numbered section of a cluster file. If an assumption set is not covered by the corpus, raise `UnclassifiedVariant` — that is a correct outcome, not a failure.

**Environment setup**

```bash
pip install -e . --break-system-packages
pip install pytest pytest-cov --break-system-packages
python -m pytest -q
```

Current baseline state: **23 tests, 1 failing** (`tests/test_multiobjective.py::test_independence_gate`), coverage 73.5%.

**Section-number map** — use these exact citation strings; they are verified against the restored clusters:

| Topic | Correct citation |
|---|---|
| Finite-n argmax | `c01 §4.1` |
| Asymptotic 1/e | `c01 §5` |
| Threshold Rule, `t_k` | `c01 §6` |
| Recall / rejection variants | `c01 §7` |
| Invalid-condition table | `c01 §8` |
| Cost-aware threshold | `c01 §9` |
| Parking | `c01 §10` |
| Burglar ceiling | `c01 §11` |
| Dominance / efficient frontier | `c02 §2.4` |
| Preferential independence | `c02 §3.3` |
| Additive value function | `c02 §3.4` |
| Utility independence | `c02 §5.1` |
| n-attribute multiplicative/additive | `c02 §5.3` |
| Scaling constants are not weights | `c02 §5.4` |
| Independence assumption registry | `c02 §7.3` |
| Flip test | `c02 §7.5` |
| Consistency audit | `c02 §7.8` |
| Bayes update | `c03 §1` |
| MDP tuple / Markov constraint | `c03 §3` |
| Bellman optimality, value iteration | `c03 §6` |
| POMDP belief update | `c03 §9` |
| Belief-state Bellman backup | `c03 §10` |

---

## T0 — Reconcile the `c01` §10 parking formula with the code (BLOCKING)

**Why first:** the corpus and the code now state different formulas for the same quantity. `AGENTS.md` declares the corpus authoritative, so as it stands the code is in violation of its own governing document. Everything downstream that cites `c01 §10` is unsound until this is resolved.

**Current state**

- `references/clusters/c01-optimal-stopping.md` §10 (line ~295) states:
  `d* = floor(-log 2 / log(1-p))` where `p` is the **occupancy rate**.
- `src/dominant_circuit/engines/stopping.py::parking_cutoff` implements:
  `floor(-log 2 / log p)`.

The manual restore of `c01` reverted the D-03 correction; the code kept it. They must agree.

**The evidence that the code is right and the corpus is wrong**

| occupancy `p` | corpus formula `-log2/log(1-p)` | code formula `-log2/log p` |
|---|---|---|
| 0.50 | 1 | 1 |
| 0.85 | 0 | 4 |
| 0.90 | 0 | 6 |
| 0.95 | 0 | 13 |
| 0.99 | 0 | 68 |

The corpus formula returns **0 for every occupancy ≥ 0.75** and *decreases* as occupancy rises. §10's own **Invariant** paragraph, three lines below the formula, states the opposite ("higher occupancy rate → larger cutoff distance"), and its worked claim that 90% → 95% "roughly doubles the expected search length" is reproduced only by the code form (ratio 2.054, versus undefined for the corpus form). The derivation in the surrounding prose — the probability that `d` consecutive spots are all occupied is `p^d`, set `p^d = 1/2` — yields the code form directly.

**Required change** — edit `references/clusters/c01-optimal-stopping.md` §10 **only**, making exactly these three edits and nothing else in the file:

1. Change the display formula from `\log(1-p)` to `\log p`.
2. Immediately after the formula, add the one-line derivation:
   > (The probability that \(d\) consecutive spots are all occupied is \(p^d\); setting \(p^d = 1/2\) and solving yields the expression above.)
3. Add the worked-values table from the right-hand column above, labelled **Worked values**.

Do not touch §§1–9 or §11 or any other part of the file. Verify with `git diff --stat` that exactly one file changed and the insertion count is under 15 lines.

**Done when**

```bash
git diff --numstat references/clusters/c01-optimal-stopping.md   # 1 file, < 15 insertions
grep -c 'log(1-p)' references/clusters/c01-optimal-stopping.md   # 0
python -c "from dominant_circuit.engines.stopping import parking_cutoff as f; print([f(p) for p in (.5,.85,.9,.95,.99)])"
# must print [1, 4, 6, 13, 68]
```

---

## T1 — Update `SKILL.md` and `AGENTS.md` (punch-list item 1)

**Why this is the highest-value task after T0:** `SKILL.md` is the file the host AI actually loads. Its orchestration block currently instructs the host to call **five functions that do not exist**, so a host following the skill faithfully will fail or silently improvise. The engines can be perfect and the product will still not work.

### T1.1 — `SKILL.md`, "Compact orchestration (Python-computable)" block

Verified as of baseline: of the functions named in that block, `verify_preconditions`, `run_validation_invariants`, and `additive_value` exist; **`select_stopping_rule`, `independence_verified`, `belief_update` (as called), `belief_greedy_action`, and `greedy_policy` do not.**

Replace the entire fenced block with code that calls only the real public API. The replacement must be executable as written:

```python
from dominant_circuit import (
    InputContract, Job, dispatch,
    missing_fields, next_question,
    ContractIncomplete, PreconditionViolation, UnclassifiedVariant, AuditFailure,
)

# Stage 1 — elicit. The library never asks; the host asks.
contract = InputContract(job=Job.STOPPING)
while (q := next_question(contract)) is not None:
    ...  # host puts q to the user, records the answer on `contract`

# Stages 2-5 — verify, compute, audit, report. One call.
report = dispatch(Job.STOPPING, contract)

print(report.to_markdown())          # full six-field Output Contract
report.decision, report.formula_name, report.citation
report.numeric, report.assumptions, report.sensitivity, report.audit
```

Immediately below the block, add this host protocol verbatim:

> **Host protocol (mandatory).**
> Drive elicitation with `missing_fields()` / `next_question()`. Do not fill contract fields on the user's behalf, and do not infer a value the user did not state — an assumption the user never made is the failure this system exists to prevent.
> `ContractIncomplete` carries `.field` and `.remedy`; put `.remedy` to the user and retry. Do not work around it.
> `PreconditionViolation` (and its subclasses `NoOptimalStoppingRuleExists`, `NonMarkovProcess`, `IndependenceNotVerified`) means the problem as stated is not computable. Report `.remedy`. Do not substitute a nearby problem that is computable.
> `UnclassifiedVariant` means the corpus does not cover this assumption set. Say so plainly. **Do not supply a constant from memory.**
> `AuditFailure` means a validation invariant failed. Report the failed invariant IDs. Do not present the decision as actionable.
> If `import dominant_circuit` fails, say that the engine is unavailable and that any figure you give is unaudited. Do not compute silently in prose.

### T1.2 — `SKILL.md`, "Core formulas (exact, by cluster)" section

Leave the formulas in place — they are useful when no interpreter is available — but add this line at the head of the section:

> **Reference only.** These are for recognition and explanation. Any number reported to a user must come from `dispatch()`. If you computed by hand because no interpreter was available, label the result **UNAUDITED** and name the invariants that were not checked.

### T1.3 — `SKILL.md`, elicitation loop

The 8-question Socratic loop currently has no question for `payoff_diverges` or `markov_verified`, both of which are hard-required by `missing_fields()`. Add them, worded to match `QUESTION_BANK` in `src/dominant_circuit/core/elicit.py`:

- "Does the expected reward grow without bound if you never stop (e.g. triple-or-nothing with full re-wagering)?" → `payoff_diverges`
- "Does the next state depend only on the current state and your action, or does the earlier history matter?" → `markov_verified`

Keep `QUESTION_BANK` and `SKILL.md` in sync; T7 adds a test that enforces this.

### T1.4 — `AGENTS.md`

1. Replace the Directory Map with the real tree (`core/` and `engines/` contain the modules listed in §3 of `SPEC.md`; `tests/` currently holds four files). Generate it from `find . -not -path './.git/*' -type f | sort` rather than by hand.
2. Under **Pairing Rule**, add:
   > The `dominant_circuit` package is a pure, non-interactive library. It performs no I/O and asks no questions. All conversation is the host's responsibility.
   > Install with `pip install -e .` from the repository root before use. If the import fails, the host must say the engine is unavailable rather than computing in prose.
3. Add:
   > If a cluster file required by the query is missing or does not cover the elicited assumption set, refuse the query and say so. Never answer from `SKILL.md`'s inlined formulas while citing a cluster section — that produces a real-looking citation for a number the corpus does not support.
4. Correct the **Engineering Invariants** section: it currently claims all hard preconditions are "enforced in code before any formula runs." After T2 that is true of INV-1…INV-6; INV-7 remains conditional. State what is actually enforced and cite the invariant IDs.

**Done when**

```bash
# every function named in SKILL.md's orchestration block is importable
python - <<'PY'
import re, builtins, dominant_circuit as d
block = re.search(r'## Compact orchestration.*?```python(.*?)```',
                  open('SKILL.md').read(), re.S).group(1)
names = set(re.findall(r'\b([a-z_][a-z0-9_]*)\s*\(', block))
names -= set(dir(builtins))          # sum, print, ...
names -= {'get', 'rule'}             # dict/local method calls, not API
missing = sorted(n for n in names if not hasattr(d, n))
print("MISSING:", missing)           # must be []
PY
```

For reference, running this against the baseline reports:
`MISSING: ['belief_greedy_action', 'greedy_policy', 'independence_verified', 'multiplicative_utility', 'select_stopping_rule']`

Note that `multiplicative_utility` *does* exist in `engines/multiobjective.py` but is not re-exported at package level — either export it in `__init__.py` or stop naming it in the orchestration block. Do not leave it half-exposed.

Promote this check into `tests/test_corpus.py` (T5) as `test_skill_orchestration_symbols_exist` so it cannot regress.

---

## T2 — Make INV-1 and INV-5 real checks (punch-list item 2)

**Current state:** in `src/dominant_circuit/core/audit.py` and in every `OutputReport` constructed by `engines/stopping.py`, INV-1 is emitted as a hardcoded literal:

```python
InvariantResult("INV-1", "assumption_set_match", True, message="...")
```

INV-5 is likewise hardcoded `True`. These are the two invariants that carry the entire anti-cargo-cult premise, and they currently report PASS without inspecting anything.

### T2.1 — Calibration registry

Add to `src/dominant_circuit/engines/stopping.py`:

```python
@dataclass(frozen=True)
class Calibration:
    """The assumption set a constant was derived under. c01 §8 / Decision Table."""
    rule: str
    citation: str
    horizon: Optional[Horizon]
    information: Optional[Information]
    payoff: Optional[Payoff]
    recall_allowed: Optional[bool]
    recall_accept_prob: Optional[float]   # None = not applicable
    rejection_prob: Optional[float]
    constant: Optional[float]             # 0.37 / 0.58 / 0.61 / 0.25 / ... ; None if exact

CALIBRATIONS: dict[str, Calibration] = { ... }
```

Populate one entry per row of `c01`'s Decision Table — ten rows. Transcribe them; do not derive them.

### T2.2 — The check

```python
def check_assumption_set_match(contract: InputContract,
                               calibration: Calibration) -> InvariantResult:
    """INV-1. Compare the elicited assumption tuple against the calibration record
    of the constant actually dispatched. Any mismatch on a field the calibration
    pins is a FAILURE, with both tuples in the message."""
```

Comparison rules:

- A calibration field set to `None` means "not pinned by this rule" and matches anything.
- A pinned field must equal the contract's elicited value exactly (floats within 1e-9).
- `constant is None` (the exact finite-n path) always passes the constant check, since nothing was reused.
- On failure, `message` must contain both the calibration tuple and the elicited tuple, so the report is self-explanatory.

Every `OutputReport` in `engines/stopping.py` must call this instead of emitting a literal. Thread the `Calibration` used through from `select_*`/branch logic.

### T2.3 — INV-5

```python
def check_range_fixed_weights(contract: InputContract) -> InvariantResult:
    """INV-5. Every key in scaling_constants must have a matching AttributeRange
    in contract.attributes with worst != best. Report the offending key(s)."""
```

Replace the hardcoded INV-5 in `core/audit.py` with this. Note `core/verify.py` already performs a similar check as a *precondition*; keep both — verify blocks before computing, audit records the result in the report.

### T2.4 — Regression tests

Add to `tests/test_stopping.py`:

```python
def test_inv1_fails_on_mismatched_calibration():
    """Hand a rule its calibration record and a contract that contradicts it."""
    # must produce InvariantResult(passed=False) with both tuples in .message

def test_inv1_is_not_hardcoded_true():
    """Statically assert no InvariantResult('INV-1', ..., True) literal remains."""
    src = Path("src/dominant_circuit").rglob("*.py")
    for f in src:
        assert 'InvariantResult("INV-1"' not in f.read_text() or "check_assumption_set_match" in f.read_text()
```

**Done when** a contract whose elicited assumptions contradict the dispatched constant produces `AuditFailure`, and `grep -rn '"INV-1", "assumption_set_match", True' src/` returns nothing.

---

## T3 — Raise `UnclassifiedVariant` when recall and rejection are both set (punch-list item 3)

**Current state, verified:** in `engines/stopping.py::solve_stopping`, the `FIXED_KNOWN` branch tests recall before rejection:

```python
if contract.recall_allowed and contract.recall_accept_prob is not None:
    ...   # 0.61
elif contract.rejection_prob is not None and contract.rejection_prob > 0:
    ...   # 0.25
```

A contract with `recall_allowed=True, recall_accept_prob=0.5, rejection_prob=0.5` silently returns r=61 under "Look-Then-Leap + fallback recall," with INV-1 reporting PASS. No row of `c01`'s Decision Table covers simultaneous recall and rejection risk; `c01` §7's Invariant explicitly warns not to conflate the two, since they move the boundary in opposite directions.

**Required change:** before the recall/rejection branch, insert an explicit guard:

```python
recall_active = bool(contract.recall_allowed) and contract.recall_accept_prob is not None
rejection_active = contract.rejection_prob is not None and contract.rejection_prob > 0
if recall_active and rejection_active:
    raise UnclassifiedVariant(
        "c01's Decision Table has no row for simultaneous recall and rejection risk. "
        "The two move the look/leap boundary in opposite directions (c01 §7 Invariant) "
        "and their combination is not calibrated in the corpus.",
        remedy="Set rejection_prob=0 (or recall_allowed=False), or supply a source "
               "that calibrates the joint case.",
        field="recall_allowed",
    )
```

Then audit the whole `solve_stopping` function for other silent-precedence paths and apply the same treatment. Specifically check: `Payoff.RUIN_RISK` currently raises `UnclassifiedVariant` even though `burglar_ceiling()` is implemented — wire it up properly by adding `q` and `m` to the contract (`ruin_success_prob`, `ruin_mean_gain`), required via `missing_fields` when `payoff == RUIN_RISK`, and cite `c01 §11`.

**Done when**

```python
def test_recall_and_rejection_both_set_raises():
    with pytest.raises(UnclassifiedVariant):
        dispatch(Job.STOPPING, contract_with(recall_allowed=True,
                 recall_accept_prob=0.5, rejection_prob=0.5))
```

passes, and `test_ruin_risk_returns_burglar_ceiling` passes.

---

## T4 — Independence: registry coverage, flip test, and `None` vs `[]` (punch-list item 4)

**Important correction to the framing.** `c02` §7.5 (restored) makes clear that the flip test does **not** establish independence — it discriminates *additive vs. multiplicative form within an already-verified independence structure*, and `run_flip_test` raises if `mutual_utility_independence_verified` is False. The coverage check is a separate function, `mutual_independence_holds`, given in `c02` §7.3. So this task is three changes, not one.

### T4.1 — Adopt the corpus data structures

`core/contract.py` currently defines `IndependenceTest(pair, method, passed, responses, notes)`. `c02` §7.3 defines the authoritative structure as `IndependenceAssumption(subset, complement, kind, verified, evidence)`. **The corpus wins.**

Add `IndependenceAssumption` to `core/contract.py`, transcribed from `c02` §7.3. Keep `IndependenceTest` as a deprecated alias for one release with a conversion helper, or remove it and update the four call sites — your choice, but state which in the commit message. Export the new name from `__init__.py`.

### T4.2 — Replace `any` with corpus-defined coverage (the "any → all" fix)

`core/verify.py:29` currently reads `if not any(t.passed for t in tests)`. One passing test among five failures clears the gate.

Implement `mutual_independence_holds(assumptions, all_attrs, kind)` in `engines/multiobjective.py`, transcribed from `c02` §7.3 — it requires **every proper nonempty subset** to be verified independent of its complement. Rewrite the `verify.py` gate to call it:

```python
attrs = frozenset(a.name for a in contract.attributes)
kind = "utility" if contract.job_is_under_uncertainty else "preferential"
if not mutual_independence_holds(contract.independence_assumptions, attrs, kind):
    raise IndependenceNotVerified(
        "Mutual independence is not covered by the assumption registry: "
        f"missing subsets {sorted(...)}.",
        remedy="Elicit and record an IndependenceAssumption for each listed subset (c02 §7.3).",
        field="independence_assumptions",
    )
```

The error message must **name the specific uncovered subsets**. `c02` §3.4 notes the n=3 special case where pairwise implies mutual; implement that shortcut and cite it.

### T4.3 — Implement the flip test

Add `run_flip_test(preferred_pairing, mutual_utility_independence_verified) -> FlipTestResult` to `engines/multiobjective.py`, transcribed from `c02` §7.5 including its `ValueError` guard and the `k_yz_sign` mapping (`None`→additive/0, `'straight'`→multiplicative/+1, `'crossed'`→multiplicative/−1).

Then use it as the form discriminator. Engine B currently routes on `sum(k_i) == 1` alone. Both criteria are valid and must agree — `Σk_i = 1 ⟺ k = 0 ⟺ additive` — so **make disagreement an INV-3 failure**:

```python
def check_independence_and_form(contract, flip_result, k_sum) -> InvariantResult:
    """INV-3. (a) registry coverage holds; (b) the recorded flip test's implied_form
    agrees with the form implied by sum(k_i). Disagreement means the elicitation is
    internally inconsistent — surface it, do not average it away (c02 §7.8)."""
```

This is a real consistency check of the kind `c02` §7.8 asks for, and it is exactly the sort of contradiction the product is supposed to catch.

### T4.4 — Split `None` from `[]`

This is the cause of the currently failing `test_independence_gate`. `core/elicit.py:60` uses `if not contract.independence_tests`, which is truthy-false for both `None` (never asked) and `[]` (asked, nothing recorded). Stage 1 therefore raises `ContractIncomplete` and Stage 2's `IndependenceNotVerified` is unreachable.

Fix: `missing_fields` must test `is None` only.

```python
if contract.independence_assumptions is None:
    missing.append("independence_assumptions")     # never elicited -> Stage 1
# an empty list means "elicited, nothing verified" -> falls through to Stage 2
```

Apply the same `is None` discipline to every other field check in `missing_fields`: `attributes`, `scaling_constants`, `states`, `actions`. An empty collection is elicited data, not absence of data. Then confirm `tests/test_multiobjective.py::test_independence_gate` passes **unmodified** — if it needs changing, you have misread the intent.

**Done when** the full suite is green including the previously failing test, and:

```python
def test_partial_coverage_rejected():
    """3 attributes, only one pair recorded -> IndependenceNotVerified naming the gaps."""
def test_flip_test_requires_prior_independence():
    with pytest.raises(ValueError):
        run_flip_test("straight", mutual_utility_independence_verified=False)
def test_form_disagreement_is_audit_failure():
    """flip test says additive, sum(k_i)=1.3 -> INV-3 fails."""
```

---

## T5 — Add `tests/test_corpus.py` (punch-list item 5)

**Why:** this file would have caught both prior failures on its own — the `c01` truncation (223 lines silently deleted) and the unresolvable `c03 §Bellman` / `c03 §belief` citations. It is cheap insurance against the corpus and the code drifting apart.

Create `tests/test_corpus.py` with at least these tests:

```python
CLUSTERS = {"c01": "c01-optimal-stopping.md",
            "c02": "c02-multiple-objectives.md",
            "c03": "c03-sequential-decisions.md"}

def test_all_clusters_exist(): ...

def test_cluster_minimum_sizes():
    """Guards against silent truncation. Floors set ~10% below the restored sizes:
       c01 >= 350 lines, c02 >= 600, c03 >= 480.
       If a cluster legitimately shrinks, this test must be updated in the SAME
       commit, with the reason in the commit body."""

def test_required_sections_present():
    """Each cluster has: Scope/Purpose, a Compact Worked Algorithm (or Compact
       Worked Example), a Decision Table (or Validation Constraints), and a
       Key Invariants (or Validation Invariants) section."""

def test_every_emitted_citation_resolves():
    """Extract every citation= and cite= string literal from src/**/*.py.
       Parse 'cNN §X[.Y]'. Assert the cluster file exists AND contains a heading
       whose number matches X[.Y]. A citation like 'c03 §Bellman' must FAIL."""

def test_no_dangling_internal_links():
    """Every relative markdown link in SKILL.md, README.md, AGENTS.md resolves
       to a file that exists."""

def test_no_pointers_to_removed_content():
    """No cluster may contain the phrases 'original corpus', 'see the original',
       or 'removed for brevity' — the tell that content was stripped and replaced
       with a pointer to something no longer present."""

def test_parking_formula_matches_code():
    """c01 §10 must contain '\\log p' and must NOT contain '\\log(1-p)'.
       Locks T0 in place."""

def test_skill_question_bank_parity():
    """Every field in elicit.QUESTION_BANK appears somewhere in SKILL.md's
       elicitation section, and vice versa. Keeps T1.3 from rotting."""
```

The citation extractor should be a small module-level helper so T6 can reuse it.

**Done when** `python -m pytest tests/test_corpus.py -v` is green, and deliberately introducing `citation="c03 §Bellman"` makes it red.

---

## T6 — Fix the unresolvable citations

Two citation strings in `engines/sequential.py` do not resolve to numbered sections:

| Current | Correct |
|---|---|
| `c03 §Bellman` | `c03 §6` (Bellman Optimality Equation, Q-Function, Value Iteration) |
| `c03 §belief` | `c03 §9` (Uncertainty over State: POMDP, Observation Model, Belief Update) |

Fix both. Then run T5's `test_every_emitted_citation_resolves` across the whole of `src/` and fix anything else it surfaces. Engine B's citations (`c02 §5.3`, `c02 §5.3 (additive special case)`) resolve correctly; normalize the parenthetical into a separate `formula_name` rather than embedding prose in the citation string.

---

## T7 — Fix the broken CI workflow

`.github/workflows/python-app.yml` is the unmodified GitHub default template and **cannot pass**:

1. It never installs the package (`pip install -e .`), so every `import dominant_circuit` in the test suite fails.
2. `pyproject.toml` sets `addopts = "--cov=dominant_circuit --cov-fail-under=55"`, but the workflow installs only `flake8 pytest` — no `pytest-cov` — so pytest aborts with `unrecognized arguments: --cov`.

Required changes to the workflow:

```yaml
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flake8 pytest pytest-cov
        pip install -e .
```

Also raise the coverage floor in `pyproject.toml` from **55 → 80**. `SPEC.md` §15.6 specified 85; the tasks above add substantial covered code, so 80 is a realistic step that still ratchets. Do not lower a coverage gate to make a build pass — add tests.

**Done when** the workflow file, run locally via the same commands, produces a green suite and the coverage gate holds.

---

## T8 — Small correctness items

Each of these is a one-to-few-line fix. Group them into a single commit.

**T8.1 — LaTeX renders with literal double backslashes.** `engines/stopping.py` lines ~181, 186, 197, 238 use raw strings containing `\\approx`, `\\quad`, `\\max`. In a raw string `r"\\approx"` is *two* characters of backslash followed by `approx`, so reports render `\\approx` literally. Use single backslashes inside `r"..."`: `r"r \approx 0.61 n"`. Sweep all `formula_latex` and `latex` assignments across all three engines.

**T8.2 — Negative `search_cost` silently accepted.** `cost_aware_threshold` does `c = max(0.0, min(0.5, c_normalized))`, so `c = -5.0` clamps to 0 and returns a threshold of 1.0 — the top of the range — for a physically meaningless input. Raise `ValueError` for `c < 0`. Keep the upper clamp at 0.5, since `c01` §9 states that a cost at or above half the range collapses the threshold to the bottom; document that clamp in the docstring.

**T8.3 — Cardinal branch ignores `n`.** `solve_stopping`'s `Information.CARDINAL` path builds `{k: threshold_percentile(k) for k in range(0, 11)}` — hardcoded 0–10 regardless of pool size, and `decision` is the bare string `"threshold_schedule"`. Build the schedule over the actual `n` (`k = n - i` for `i` in `1..n`), and add the `threshold_rule(n, scores=None)` function from `SPEC.md` §7.1 so that supplying scores returns the accepted index. Cite `c01 §6`.

**T8.4 — `classify_job` missing.** `SPEC.md` §5 requires it and `SKILL.md` should be able to reference it. Implement in `core/elicit.py`, classifying **from contract fields only** — never from substring matching on user prose, which is the D-06 defect that the rewrite was meant to eliminate. Raise `ContractIncomplete(field='job')` when the fields do not determine the job.

**T8.5 — `dominance_screen` missing.** `SKILL.md`'s anti-cargo-cult rules state "Never skip dominance screening before running full preference elicitation." `c02` §2.4 and §7.2 give the algorithm. Implement it in `engines/multiobjective.py` and call it at the top of `solve_multiobjective`, recording the count of screened-out alternatives in `report.numeric`.

---

## T9 — Guard against unannounced deletion

**Why:** commit `a2d99aa` was titled "Correct c01 §10 parking formula" and deleted 223 lines of corpus. Nothing caught it. T5 adds size floors on the clusters; this task extends the same protection to the public API.

Add `tests/test_api_surface.py`:

```python
EXPECTED_EXPORTS = { ... }   # the full __all__ as of completion of T8

def test_public_api_surface_is_stable():
    """Removing a public export must be a deliberate, visible act. If this test
    fails because you intentionally removed a symbol, update EXPECTED_EXPORTS in
    the SAME commit and state the removal in the commit body."""
    assert set(dominant_circuit.__all__) >= EXPECTED_EXPORTS
```

Also add to `AGENTS.md` a short **Change discipline** section:

> Deleting corpus content or public API symbols requires an explicit line in the commit body beginning `REMOVES:`. A commit whose stated purpose is a fix must not also delete unrelated content.

---

## Acceptance criteria for the whole punch list

Run from a clean clone:

```bash
pip install -e . --break-system-packages
pip install pytest pytest-cov --break-system-packages
python -m pytest -q
```

1. Suite green, **zero failures**, coverage ≥ 80%.
2. `tests/test_corpus.py` passes; every citation emitted anywhere in `src/` resolves to a real numbered cluster section.
3. `c01` §10 and `parking_cutoff` agree; `[f(p) for p in (.5,.85,.9,.95,.99)] == [1,4,6,13,68]`.
4. Every function named in `SKILL.md`'s orchestration block is importable from `dominant_circuit`.
5. `grep -rn '"INV-1", "assumption_set_match", True' src/` returns nothing; a contradicting contract produces `AuditFailure`.
6. `recall_allowed=True, recall_accept_prob=0.5, rejection_prob=0.5` raises `UnclassifiedVariant`.
7. `tests/test_multiobjective.py::test_independence_gate` passes **unmodified**.
8. Partial independence coverage is rejected with the uncovered subsets named.
9. `python main.py < /dev/null` exits 0 and prints complete reports.
10. `grep -rn 'input(' src/ --include='*.py'` returns nothing.
11. The four product-intent tests from `SPEC.md` §15.7 all pass — in particular, all four, not three.

## Sanity check on golden values

These were verified against the restored corpus and must still hold after every task. If any changes, you have broken something:

| Check | Expected |
|---|---|
| `optimal_cutoff(100)` | `(38, 0.371043)` |
| `optimal_cutoff(1000)` | `(369, 0.368196)` |
| `optimal_cutoff(n)` for n=1..10 | r\* = 1,1,2,2,3,3,3,4,4,4 |
| `asymptotic_cutoff(100)` | `(37, 1/e)` — deliberately differs from exact |
| `threshold_percentile(1,2,3)` | 0.5033, 0.6907, 0.7762 |
| `parking_cutoff(.9,.95,.99)` | 6, 13, 68 |
| `parking_cutoff_exact(.95)/parking_cutoff_exact(.90)` | 2.054 |
| `cost_aware_threshold(0,1,0.02)` | 0.80 |
| `burglar_ceiling(0.9, 1.0)` | 9.0 |
| `cutoff_unknown_horizon_uniform(1000)[0]` | 135 |
| `cutoff_stochastic_stop(0.01)[0]` | 18 |

---

## Out of scope

Do not, in this pass: add a web UI, add persistence, make anything async, introduce new dependencies beyond `pytest-cov`, or extend the corpus with material from sources not listed in `NOTICE.md`. If a task appears to require any of these, stop and report instead.
