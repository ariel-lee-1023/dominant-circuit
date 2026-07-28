# Dominant-Circuit — Implementation Specification v1.0

**Repository:** https://github.com/ariel-lee-1023/dominant-circuit
**Baseline audited:** commit `a66504d` ("Add zero-order calculating machine: solvers.py, engine.py, main.py under src/dominant_circuit/")
**Author of spec:** Ariel Lee
**Date:** 2026-07-27
**Status:** Ready for implementation

---

## 0. How to read this document

This is a build specification, not a code review. It states what the repository must contain when the work is done.

- **§1** restates the product design and binds each of its five stages to a specific code artifact that must own it.
- **§2** is the defect register against the current commit. Every defect has an ID; every requirement later in this document references the defect IDs it closes.
- **§3–§10** are the code contracts: module layout, dataclasses, function signatures, error taxonomy, and the exact mathematics each function must implement. Signatures are normative — do not rename them, because `SKILL.md` and the host AI's dispatch instructions will be written against them.
- **§11** specifies the two missing corpus files the engineer must author.
- **§12** is a mathematical correction to existing corpus content.
- **§13** lists documentation that currently describes software that does not exist and must be corrected.
- **§14** is the test suite with golden numeric values, all independently verified. These are the acceptance oracle.
- **§15–§17** are acceptance criteria, sequencing, and non-goals.

Where this document and any existing file in the repository disagree, **this document wins**, except for `references/clusters/c01-optimal-stopping.md`, which is the mathematical source of truth for Engine A and is only overridden where §12 says so explicitly.

**Governing design principle, stated once and applying everywhere below:** the Python package is a *pure, non-interactive computation library*. It performs no I/O, asks no questions, and never blocks on input. The host AI is the conversational front-end; the library is the physics engine it calls. Every function must be callable, deterministic (given a seed where randomness is involved), and testable without a terminal.

---

## 1. Product intent and stage ownership

The product is a five-stage pipeline that converts a vague human dilemma into an audited, mathematically optimal recommendation. The stages, and the artifact that must own each:

| Stage | Intent | Owning artifact | Currently owned by |
|---|---|---|---|
| 1. Elicitation | Refuse to compute until the Input Contract is complete; interrogate the user for horizon, information type, recall/rejection, risk attitude, budget | `SKILL.md` (question script) + `core/elicit.py` (completeness checker) | `engine.run_socratic_loop`, via blocking `input()` — unusable |
| 2. Verification | Block computation when the parameters violate mathematical preconditions | `core/verify.py` | `engine.verify_preconditions` — two checks, one unreachable |
| 3. Computation | Route validated inputs to the correct zero-order formula | `core/dispatch.py` → `engines/` | `solvers.py` — 1 of 3 engines, partial |
| 4. Audit | Prove the work before showing it; loop back to Stage 1 on failure | `core/audit.py` | Nothing. Function referenced in `SKILL.md`, does not exist |
| 5. Reporting | Emit decision + formula + assumptions + sensitivity + audit results | `core/report.py` | Raw solver dict, 2 of 6 required fields |

The four sentences below are the acceptance test for "does this feel like the product":

1. A host AI that has *not* collected the full contract must be structurally unable to obtain a number from this library — it must get a `ContractIncomplete` error naming the missing field.
2. A host AI that supplies a physically impossible problem must get a `PreconditionViolation` naming the violated law, not an answer.
3. Every number the library returns must arrive attached to the assumption set that makes it valid, and must be different if the assumption set is different.
4. No answer may be returned with a failed invariant hidden inside it.

---

## 2. Defect register (baseline `a66504d`)

Severity: **S1** blocks the product design outright · **S2** silently produces wrong or unattributed results · **S3** correctness/robustness · **S4** documentation and hygiene.

### Corpus

| ID | Sev | File | Defect |
|---|---|---|---|
| D-01 | S1 | `references/clusters/` | `c02-multiple-objectives.md` does not exist. `SKILL.md` links to it; the link 404s. Engine B has no source of truth. |
| D-02 | S1 | `references/clusters/` | `c03-sequential-decisions.md` does not exist. `SKILL.md` links to it; the link 404s. Engine C has no source of truth. |
| D-03 | S2 | `c01` §10 | Parking cutoff given as `d* = floor(-log 2 / log(1-p))`. As written this returns **0 for every occupancy ≥ 0.75** and *decreases* with occupancy, directly contradicting the invariant stated two lines below it. See §12. |

### Stage 1 — Elicitation

| ID | Sev | File | Defect |
|---|---|---|---|
| D-04 | S1 | `engine.py:19–30` | `run_socratic_loop` calls `input()`. A host AI cannot drive this. `main.py` dies with `EOFError` on any non-TTY invocation. Verified. |
| D-05 | S1 | `engine.py:16–30` | Collects 3–4 of the 8 Input Contract fields. Horizon type, recall, rejection, risk attitude, search cost, compute budget, attribute ranges are never captured. |
| D-06 | S1 | `engine.py:17,23` | Job routing is substring matching on `"stop"`/`"looking"`/`"tradeoff"`/`"objectives"`. No `sequential` branch. Unmatched input leaves `job = None`, producing `NotImplementedError` from `dispatch`. |
| D-07 | S2 | `engine.py:25` | Independence is captured as a yes/no self-report string. No flip test is implemented. The precondition is satisfiable by typing "yes". |

### Stage 2 — Verification

| ID | Sev | File | Defect |
|---|---|---|---|
| D-08 | S1 | `engine.py:21` | `self.contract['infinite_payoff'] = False` is hardcoded, with the comment "Ask user if rewards diverge." The diverging-payoff blocker — the product design's headline Stage 2 example — is **unreachable**. |
| D-09 | S1 | `engine.py` | No Markov check exists anywhere, despite being listed as a hard precondition blocker in `README.md` and `SKILL.md`. |
| D-10 | S2 | `engine.py` | No over-determination check (`SKILL.md` invariant 7). Inconsistent elicitation cannot be detected. |
| D-11 | S2 | `engine.py` | No range-attachment check on scaling constants (`SKILL.md` invariant 5). |

### Stage 3 — Computation

| ID | Sev | File | Defect |
|---|---|---|---|
| D-12 | S1 | `solvers.py` | No sequential/MDP/POMDP code at all. No Bellman backup, no value iteration, no belief update. The Bellman equation is the product description's headline formula. |
| D-13 | S2 | `solvers.py:29` | Multiplicative multiattribute form is unimplemented. `SKILL.md` specifies it as the correct form when Σkᵢ ≠ 1; the code instead **raises** on that exact condition. The documented fallback path is an error path. Verified. |
| D-14 | S2 | `solvers.py:16` | Uses asymptotic `round(n/e)` for all n, ignoring the exact finite-n argmax that `c01` §4.1 supplies. At n=100 this yields r=37; the exact argmax is **r\*=38**. Verified off-by-one. |
| D-15 | S2 | `solvers.py:13` | `rejection_prob > 0 → 0.25n` for *any* p. The 0.25 constant is calibrated for p=0.5 only. Directly violates `SKILL.md` validation invariant 1 ("reusing 37%, 58%, 61%, or 25% outside their calibrated assumption set is an audit failure"). |
| D-16 | S2 | `solvers.py:11` | Recall branch hardcodes 0.61 with no `recall_accept_prob` parameter. `c01` §7 explicitly warns: "do not reuse 0.61 for other acceptance probabilities." |
| D-17 | S2 | `solvers.py:21–25` | Cardinal branch returns prose with **no number**. The 58% Threshold Rule and the `t_k` formula, both fully specified in `c01` §6, are never computed. Verified. |
| D-18 | S1 | `solvers.py` | Unimplemented despite being fully specified in `c01`: unknown-horizon cutoffs (§8), stochastic-termination cutoff (§8), cost-aware threshold (§9), parking (§10), burglar ceiling (§11). `recall`/`rejection_prob` parameters exist but are unreachable because Stage 1 never elicits them. |

### Stage 4 — Audit

| ID | Sev | File | Defect |
|---|---|---|---|
| D-19 | S1 | — | `run_validation_invariants()` is called in `SKILL.md`'s orchestration pseudocode and **does not exist**. |
| D-20 | S1 | `engine.dispatch` | Audit is never invoked. `dispatch` returns the solver dict directly. Violates the repository's own rule: "Never report a decision without its audit results." |
| D-21 | S2 | `solvers.py:44` | `verify_bellman_residual` accepts `gamma` and never uses it, returns a bare float, has no pass/fail semantics, and is called by nothing. Verified. |

### Stage 5 — Reporting

| ID | Sev | File | Defect |
|---|---|---|---|
| D-22 | S1 | `solvers.py` | Returns 2–3 of the 6 mandatory Output Contract fields. No assumptions, no sensitivity, no audit block, no cluster/section citation. |

### Packaging and documentation

| ID | Sev | File | Defect |
|---|---|---|---|
| D-23 | S1 | `README.md` | Advertised API does not exist: `from dominant_circuit import dispatch, InputContract` → `ImportError`. Verified after `pip install -e .`. |
| D-24 | S1 | `SKILL.md` | Orchestration block calls 9 functions that exist nowhere: `verify_preconditions`, `select_stopping_rule`, `independence_verified`, `additive_value`, `multiplicative_utility`, `belief_update`, `belief_greedy_action`, `greedy_policy`, `run_validation_invariants`. |
| D-25 | S3 | `main.py:2` | `from src.dominant_circuit.engine import …` breaks after `pip install -e .` (src-layout installs the package as `dominant_circuit`). |
| D-26 | S4 | `AGENTS.md` | Directory map lists `src/dominant_circuit/core/`, `src/dominant_circuit/engines/`, and `tests/`. None exist. |
| D-27 | S4 | — | No tests, despite `AGENTS.md` claiming "Smoke tests for every engine." `pyproject.toml` declares `testpaths = ["tests"]` against a directory that does not exist. |
| D-28 | S4 | `pyproject.toml` | Declares `numpy` and `scipy` dependencies; neither is imported anywhere. Declares `package-data` for `py.typed`, which does not exist. |
| D-29 | S4 | `pyproject.toml:12` | Author email is `ariel.lee.1023@example.com` — placeholder domain. |

**The failure mode that matters most.** `AGENTS.md` instructs the host AI that it "must not invent formulas outside the zero-order set documented here." With D-01 and D-02 open, no documented set exists for two of three job types — yet `SKILL.md` inlines the Bellman and multiattribute formulas in its own "Core formulas" section. The host will therefore improvise from `SKILL.md` while emitting cluster-and-section citations that do not resolve. That is confident output with fabricated provenance: precisely the cargo-cult behavior this project exists to prevent. D-01 and D-02 are the highest-priority items in this document.

---

## 3. Target repository layout

```
SKILL.md                              # Router skill — corrected per §13
AGENTS.md                             # Host-AI pairing rules — corrected per §13
README.md                             # Corrected per §13
SPEC.md                               # This document
NOTICE.md, LICENSE                    # Unchanged
pyproject.toml                        # Corrected per §13.5
references/clusters/
  c01-optimal-stopping.md             # Existing; corrected per §12
  c02-multiple-objectives.md          # NEW — authored per §11.1
  c03-sequential-decisions.md         # NEW — authored per §11.2
src/dominant_circuit/
  __init__.py                         # Public API surface, §10.2
  py.typed                            # NEW — empty marker file
  core/
    __init__.py
    contract.py                       # InputContract + enums, §4.1
    report.py                         # OutputReport, AuditResult, Sensitivity, §4.2, §9
    errors.py                         # Error taxonomy, §4.3
    elicit.py                         # Completeness checking, §5
    verify.py                         # Hard preconditions, §6
    audit.py                          # Validation invariants, §8
    dispatch.py                       # Orchestrator, §10
  engines/
    __init__.py
    stopping.py                       # Engine A, §7.1
    multiobjective.py                 # Engine B, §7.2
    sequential.py                     # Engine C, §7.3
tests/
  test_contract.py, test_verify.py, test_stopping.py,
  test_multiobjective.py, test_sequential.py,
  test_audit.py, test_dispatch.py, test_corpus.py    # §14
```

`main.py` is retained as a **demonstration CLI only**, rewritten per §13.4. It must not be imported by anything in `src/`.

---

## 4. Shared data contracts

### 4.1 `core/contract.py`

Use `@dataclass`. All fields default to `None` so that "not yet elicited" is distinguishable from "elicited as zero/false" — this distinction is what makes D-08 fixable.

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Sequence

class Job(str, Enum):
    STOPPING = "stopping"
    MULTIOBJECTIVE = "multiobjective"
    SEQUENTIAL = "sequential"

class Horizon(str, Enum):
    FIXED_KNOWN = "fixed_known"                  # n known exactly
    FIXED_UNKNOWN_UNIFORM = "fixed_unknown_uniform"   # n ~ Uniform[1, n_max]
    OPEN_ENDED_STOCHASTIC = "open_ended_stochastic"   # terminates w.p. p per step
    UNBOUNDED_STREAM = "unbounded_stream"        # cost-of-search formulations
    FINITE_SUM = "finite_sum"                    # sequential, finite horizon
    INFINITE_DISCOUNTED = "infinite_discounted"  # sequential, gamma < 1

class Information(str, Enum):
    ORDINAL = "ordinal"          # relative rank only
    CARDINAL = "cardinal"        # absolute score / percentile known

class Payoff(str, Enum):
    BEST_OR_NOTHING = "best_or_nothing"
    COST_OF_SEARCH = "cost_of_search"
    RUIN_RISK = "ruin_risk"
    AVERAGE_RANK = "average_rank"
    DURATION = "duration"
    MULTIATTRIBUTE = "multiattribute"
    DISCOUNTED_RETURN = "discounted_return"

class RiskAttitude(str, Enum):
    AVERSE = "averse"
    NEUTRAL = "neutral"
    PRONE = "prone"

@dataclass
class AttributeRange:
    """Invariant 5: a scaling constant is meaningless without its assessed range."""
    name: str
    worst: float
    best: float
    monotonic_increasing: bool = True

@dataclass
class IndependenceTest:
    """Invariant 3: a recorded, verified test — never a bare boolean."""
    pair: tuple[str, str]
    method: str              # "flip_test" | "fractile" | ...
    passed: bool
    responses: list[Any] = field(default_factory=list)
    notes: str = ""

@dataclass
class InputContract:
    job: Optional[Job] = None

    # 1. Horizon
    horizon: Optional[Horizon] = None
    n: Optional[int] = None
    n_max: Optional[int] = None
    stop_prob_per_step: Optional[float] = None   # p, OPEN_ENDED_STOCHASTIC
    gamma: Optional[float] = None                # discount, sequential

    # 2. Alternatives / states / actions
    alternatives: Optional[Sequence[Any]] = None
    states: Optional[Sequence[Any]] = None
    actions: Optional[Sequence[Any]] = None

    # 3. Objective hierarchy and ranges
    attributes: Optional[list[AttributeRange]] = None
    payoff: Optional[Payoff] = None

    # 4. Independence
    independence_tests: Optional[list[IndependenceTest]] = None
    scaling_constants: Optional[dict[str, float]] = None   # keyed by attribute name

    # 5. Uncertainty
    information: Optional[Information] = None
    transition: Optional[Callable | dict] = None      # T(s'|s,a)
    reward: Optional[Callable | dict] = None          # R(s,a)
    observation_model: Optional[Callable | dict] = None   # O(o|a,s')
    prior_belief: Optional[dict] = None
    observations: Optional[list] = None
    markov_verified: Optional[bool] = None

    # 6. Search costs / recall / rejection
    search_cost: Optional[float] = None          # normalized to [0,1] outcome scale
    recall_allowed: Optional[bool] = None
    recall_accept_prob: Optional[float] = None   # REQUIRED if recall_allowed
    rejection_prob: Optional[float] = None       # P(offer declined by candidate)

    # 7. Risk attitude
    risk_attitude: Optional[RiskAttitude] = None
    risk_varies_with_level: Optional[str] = None   # "constant"|"decreasing"|"increasing"

    # 8. Compute budget
    exact_finite_n: bool = True       # default: exact, NOT asymptotic. Closes D-14.
    k_max: int = 1000
    tolerance: float = 1e-6
    mcts_simulations: Optional[int] = None
    search_depth: Optional[int] = None

    # Divergence flag — MUST be explicitly elicited, never defaulted. Closes D-08.
    payoff_diverges: Optional[bool] = None
```

**Normative:** `payoff_diverges` and `markov_verified` must have no default value of `False`. `None` means "not asked" and must raise `ContractIncomplete`. This single rule closes D-08 and D-09.

**Normative:** `exact_finite_n` defaults to `True`. The asymptotic 1/e shortcut is opt-in, never the default. This closes D-14.

### 4.2 `core/report.py` — output types

```python
@dataclass
class InvariantResult:
    invariant_id: str        # "INV-1" .. "INV-7", see §8
    name: str
    passed: bool
    residual: Optional[float] = None
    tolerance: Optional[float] = None
    message: str = ""

@dataclass
class AuditResult:
    results: list[InvariantResult]
    @property
    def passed(self) -> bool: ...        # all(r.passed)
    @property
    def failures(self) -> list[InvariantResult]: ...

@dataclass
class SensitivityEntry:
    assumption: str          # "recall_accept_prob"
    perturbation: str        # "0.5 -> 0.3"
    new_decision: Any
    decision_changed: bool
    fragility: str           # "robust" | "fragile" | "critical"

@dataclass
class OutputReport:
    # Output Contract field 1
    decision: Any
    # field 2 — MUST include cluster + section
    formula_name: str
    formula_latex: str
    citation: str            # e.g. "c01 §4.1"
    # field 3
    numeric: dict[str, float]      # threshold, cutoff, P_n(r), U(s), belief vector...
    # field 4 — the full locked assumption set
    assumptions: dict[str, Any]
    # field 5
    sensitivity: list[SensitivityEntry]
    # field 6
    audit: AuditResult

    def to_markdown(self) -> str: ...   # §9
    def to_dict(self) -> dict: ...
```

**Normative:** `OutputReport` has no default values on `assumptions`, `sensitivity`, or `audit`. Constructing a report without them must be a `TypeError` at the language level. This makes D-22 structurally unrepeatable.

### 4.3 `core/errors.py` — error taxonomy

```python
class DominantCircuitError(Exception):
    """Base. Carries a machine-readable remediation hint for the host AI."""
    def __init__(self, message: str, *, remedy: str = "", field: str = ""):
        super().__init__(message)
        self.remedy = remedy      # what the host must ask the user
        self.field = field        # which contract field is implicated

class ContractIncomplete(DominantCircuitError):
    """Stage 1 failure. .field names the first missing field; .remedy is the question to ask."""

class PreconditionViolation(DominantCircuitError):
    """Stage 2 failure. A mathematical law is violated. Do not compute."""

class NoOptimalStoppingRuleExists(PreconditionViolation):
    """Diverging expected payoff. c01 §8. Remedy: switch to a fractional-bankroll framework."""

class NonMarkovProcess(PreconditionViolation):
    """c03. Remedy: augment the state until Markov is restored."""

class IndependenceNotVerified(PreconditionViolation):
    """c02. Remedy: run the flip test."""

class AuditFailure(DominantCircuitError):
    """Stage 4 failure. Carries .audit: AuditResult."""
    def __init__(self, message, audit, **kw): ...

class UnclassifiedVariant(DominantCircuitError):
    """No rule in the corpus matches this assumption set. Do NOT improvise."""

class NotInCorpus(DominantCircuitError):
    """The host asked for a formula the clusters do not document."""
```

**Normative:** every error must populate `remedy` with the literal question or action the host AI should take next. This is what makes Stage 4's "loop back to Stage 1" mechanical rather than aspirational.

---

## 5. Stage 1 — Elicitation (`core/elicit.py`)

Closes D-04, D-05, D-06, D-07.

The library does not ask questions. It reports what is missing, and the host AI asks. Required functions:

```python
REQUIRED_FIELDS: dict[Job, list[str]]
"""Per-job required contract fields, including conditional requirements:
   - recall_accept_prob is required iff recall_allowed is True
   - n is required iff horizon == FIXED_KNOWN
   - n_max is required iff horizon == FIXED_UNKNOWN_UNIFORM
   - stop_prob_per_step required iff horizon == OPEN_ENDED_STOCHASTIC
   - gamma required iff horizon == INFINITE_DISCOUNTED
   - observation_model + prior_belief required iff the sequential problem is a POMDP
   - payoff_diverges required for ALL stopping jobs
   - markov_verified required for ALL sequential jobs
"""

QUESTION_BANK: dict[str, str]
"""Field name -> the exact natural-language question the host AI should ask.
   Seed from SKILL.md's 8-question Socratic loop; extend to cover every field."""

def missing_fields(contract: InputContract) -> list[str]:
    """Ordered by SKILL.md's elicitation sequence. Empty list == ready to compute."""

def next_question(contract: InputContract) -> Optional[str]:
    """The single next question to ask, or None if the contract is complete."""

def require_complete(contract: InputContract) -> None:
    """Raise ContractIncomplete(field=<first missing>, remedy=QUESTION_BANK[field])
       if anything is missing. Called first by dispatch(). No exceptions, no bypass."""

def classify_job(contract: InputContract) -> Job:
    """Structural classification from contract fields ONLY.
       Substring matching on the user's prose is FORBIDDEN (closes D-06).
       If the contract does not determine the job, raise ContractIncomplete(field='job')."""
```

### 5.1 The flip test must be a real function (closes D-07)

A boolean the host can set to `True` is not a verification. Implement:

```python
def flip_test(
    attribute_pair: tuple[str, str],
    responses: list[dict],
) -> IndependenceTest:
    """Pairwise preferential independence test, per c02 §3.4 (to be authored, §11.1).

    Each response records the user's preference between two consequence pairs that
    differ on attributes (X_i, X_j) while a third attribute Z is held at level z1;
    the test is repeated with Z held at a different level z2.

    Preferential independence HOLDS iff the stated preference is invariant to the
    level of Z across all recorded response pairs.

    Returns IndependenceTest(passed=..., responses=<verbatim>, method='flip_test').
    Raises ContractIncomplete if fewer than 2 levels of Z were tested — a single
    level cannot demonstrate invariance.
    """
```

`core/verify.py` must accept only an `IndependenceTest` object produced by this function (or an equivalent recorded test), never a bare boolean.

---

## 6. Stage 2 — Verification (`core/verify.py`)

Closes D-08, D-09, D-10, D-11.

```python
def verify_preconditions(contract: InputContract) -> None:
    """Dispatch to the per-job checkers. Raises PreconditionViolation subclasses.
       Returns None on success. MUST be called by dispatch() before any engine runs."""

def check_finite_expectation(contract) -> None:
    """c01 §8 hard invalidity condition.
       if contract.payoff_diverges is None -> ContractIncomplete(field='payoff_diverges',
           remedy='Does the payoff grow without bound the longer you continue
                   (e.g. double-or-nothing with full re-wagering)?')
       if contract.payoff_diverges is True -> NoOptimalStoppingRuleExists(
           remedy='Switch to a fractional-bankroll rule such as Kelly betting.')
       Closes D-08."""

def check_independence(contract) -> None:
    """c02. Requires len(contract.independence_tests) covering every attribute pair
       used by the chosen functional form, each with .passed is True.
       Missing or failing -> IndependenceNotVerified(remedy='Run the flip test on <pair>').
       Closes D-07."""

def check_ranges_attached(contract) -> None:
    """SKILL.md invariant 5. Every key in scaling_constants must have a matching
       AttributeRange in contract.attributes with worst != best.
       Closes D-11."""

def check_markov(contract) -> None:
    """c03. if contract.markov_verified is None -> ContractIncomplete(
           remedy='Does the next state depend only on the current state and action,
                   or does history matter?')
       if False -> NonMarkovProcess(remedy='Augment the state with the history terms
                   that matter, then re-verify.')
       Closes D-09."""

def check_discount_and_bounded_rewards(contract) -> None:
    """c03. Bellman convergence requires gamma in [0,1) for infinite horizon and
       finite reward magnitudes. gamma == 1.0 with INFINITE_DISCOUNTED is a violation."""

def check_overdetermination(contract) -> None:
    """SKILL.md invariant 7. The count of recorded indifference/trade-off equations
       must EXCEED the number of free parameters (scaling constants + utility
       curve parameters). If equal, inconsistency is undetectable by construction.
       Raise PreconditionViolation(remedy='Elicit at least one additional trade-off
       so the responses can be cross-checked.'). Closes D-10."""
```

**Normative:** no engine function may be called by `dispatch` before `verify_preconditions` returns cleanly. Engines must additionally re-assert their own preconditions defensively so that direct calls remain safe.

---

## 7. Stage 3 — Computation

### 7.1 Engine A — `engines/stopping.py`

Source of truth: `c01`. Closes D-14, D-15, D-16, D-17, D-18.

```python
def p_n_r(n: int, r: int) -> float:
    """c01 §4. Exact success probability of Look-Then-Leap with cutoff r.
       P_n(r) = ((r-1)/n) * sum_{j=r}^{n} 1/(j-1)   for 2 <= r <= n
       P_n(1) = 1/n"""

def optimal_cutoff(n: int) -> tuple[int, float]:
    """c01 §4.1. Exact finite-n argmax over r in 1..n. Returns (r_star, P_n(r_star)).
       This is the DEFAULT path for FIXED_KNOWN + ORDINAL. Closes D-14."""

def asymptotic_cutoff(n: int) -> tuple[int, float]:
    """c01 §5. round(n/e), success -> 1/e. Reachable ONLY when
       contract.exact_finite_n is False. Must emit an audit note recording that an
       approximation was used, with the exact-vs-approximate delta."""

def threshold_percentile(k: int) -> float:
    """c01 §6. t_k = 1/(1 + 0.804/k + 0.183/k**2) for k >= 1; t_0 = 0.0
       k = candidates remaining AFTER the current one."""

def threshold_rule(n: int, scores: Sequence[float] | None = None) -> dict:
    """c01 §6. Full-information policy. Returns the complete threshold schedule
       {position: t_k} AND, if scores are supplied, the accepted index.
       MUST return numbers. Closes D-17."""

def cutoff_with_recall(n: int, recall_accept_prob: float) -> tuple[int, float]:
    """c01 §7. recall_accept_prob == 0.5 -> r = round(0.61*n), success ~= 0.61.
       For ANY OTHER value, r must be recomputed from the underlying optimization;
       if no recomputation is implemented, raise UnclassifiedVariant with
       remedy='0.61 is calibrated for recall_accept_prob=0.5 only (c01 §7); this
       assumption set requires recomputation.'  Silent reuse of 0.61 is FORBIDDEN.
       Closes D-16."""

def cutoff_with_rejection(n: int, rejection_prob: float) -> tuple[int, float]:
    """c01 §7. rejection_prob == 0.5 -> r = round(0.25*n), success ~= 0.25.
       Any other value -> UnclassifiedVariant, same rule as above. Closes D-15."""

def cutoff_unknown_horizon_uniform(n_max: int) -> tuple[int, float]:
    """c01 §8. r = round(n_max / e**2) ~= 0.135*n_max; success 2/e**2 ~= 0.27."""

def cutoff_stochastic_stop(p: float) -> tuple[int, float]:
    """c01 §8. r = round(0.18 / p); success ~= 0.236."""

def cost_aware_threshold(low: float, high: float, cost_normalized: float) -> float:
    """c01 §9. p* = 1 - sqrt(2c) on the normalized scale; return low + p*(high-low).
       cost_normalized >= 0.5 collapses the threshold to `low` (accept first offer).
       Raise ValueError for cost_normalized < 0."""

def parking_cutoff(occupancy: float) -> int:
    """c01 §10 AS CORRECTED BY SPEC §12.
       d* = floor(-log(2) / log(occupancy))
       Requires 0 < occupancy < 1. See §12 before implementing."""

def burglar_ceiling(success_prob_q: float, mean_gain_m: float) -> float:
    """c01 §11. ceiling = m*q/(1-q). Requires 0 <= q < 1."""

def select_stopping_rule(contract: InputContract) -> tuple[Callable, dict, str]:
    """c01 'Compact Worked Algorithm'. Returns (rule_fn, kwargs, citation).
       Dispatch on (payoff, horizon, information, recall_allowed, rejection_prob).
       Any combination not present in c01's Decision Table MUST raise
       UnclassifiedVariant. Improvising a constant is FORBIDDEN."""

def solve(contract: InputContract) -> OutputReport:
    """Engine A entry point. Full Output Contract, including sensitivity per §7.4."""
```

**Normative — the assumption-set lock.** `select_stopping_rule` must be implemented as an explicit lookup over `c01`'s Decision Table, with one row per documented assumption combination. It must not contain a fall-through `else` that reaches for a default constant. Absence of a matching row is `UnclassifiedVariant`, which the host reports honestly. This is the single most important behavioral requirement in Engine A.

### 7.2 Engine B — `engines/multiobjective.py`

Source of truth: `c02` (to be authored, §11.1). Closes D-13.

```python
def normalize_component_value(x: float, rng: AttributeRange) -> float:
    """v_i(worst) = 0, v_i(best) = 1, respecting monotonic direction."""

def dominance_screen(alternatives, attributes) -> tuple[list, list]:
    """Return (surviving, dominated). Anti-cargo-cult rule: never run full
       preference elicitation before dominance screening. Must run first."""

def additive_value(component_values: dict[str, float],
                   weights: dict[str, float]) -> float:
    """v(x) = sum_i lambda_i * v_i(x_i). Requires sum(weights) == 1 within tolerance
       AND verified preferential independence."""

def multiplicative_utility(component_utilities: dict[str, float],
                           weights: dict[str, float]) -> float:
    """1 + k*u(x) = prod_i (1 + k*k_i*u_i(x_i)), where k solves
       1 + k = prod_i (1 + k*k_i).
       Solve for k numerically (bisection or Newton) on the correct branch:
         sum(k_i) > 1 -> -1 < k < 0 ;  sum(k_i) < 1 -> k > 0.
       Additive is the k -> 0 limit. Closes D-13 — sum != 1 is a ROUTING
       condition, never an error."""

def solve_k(weights: dict[str, float], tolerance: float) -> float:
    """Root-find on f(k) = prod_i(1 + k*k_i) - (1 + k). Must return k = 0.0 when
       sum(k_i) == 1 within tolerance."""

def expected_utility(lottery: Sequence[tuple[float, dict]], ...) -> float:
    """Sum over outcomes of probability * multiattribute utility."""

def certainty_equivalent(lottery, utility_fn) -> float: ...

def assess_risk_attitude(certainty_equivalent: float,
                         expected_value: float) -> RiskAttitude:
    """CE < EV -> AVERSE; CE == EV -> NEUTRAL; CE > EV -> PRONE."""

def solve(contract: InputContract) -> OutputReport: ...
```

**Normative:** `additive_value` must never be selected because it is simpler. Selection is: run `dominance_screen` → require verified independence → inspect `sum(k_i)` → route to additive (=1) or multiplicative (≠1). Report the routing decision in `formula_name`.

### 7.3 Engine C — `engines/sequential.py`

Source of truth: `c03` (to be authored, §11.2). Closes D-12.

```python
@dataclass
class MDP:
    states: Sequence
    actions: Sequence
    transition: Callable          # T(s, a, s') -> prob
    reward: Callable              # R(s, a) -> float
    gamma: float
    def validate(self) -> None:
        """Every sum_s' T(s,a,s') == 1.0 within tolerance; gamma in [0,1);
           rewards finite. Raise PreconditionViolation naming the offending (s,a)."""

def q_value(mdp: MDP, U: dict, s, a) -> float:
    """Q(s,a) = R(s,a) + gamma * sum_s' T(s'|s,a) * U(s')"""

def bellman_backup(mdp: MDP, U: dict) -> dict:
    """U'(s) = max_a Q(s,a) for all s."""

def value_iteration(mdp: MDP, k_max: int, tolerance: float
                    ) -> tuple[dict, list[float]]:
    """Iterate backups until max residual <= tolerance or k_max reached.
       Returns (U, residual_history). residual_history feeds INV-4."""

def greedy_policy(mdp: MDP, U: dict) -> Callable:
    """s -> argmax_a Q(s,a)"""

def policy_iteration(mdp: MDP, k_max: int) -> tuple[dict, Callable]: ...

def bayes_update(prior: dict, likelihood: Callable, observation) -> dict:
    """P(x|y) = P(y|x)P(x)/P(y).
       If P(y) == 0 (zero-likelihood evidence): reset to uniform over the support
       and record an InvariantResult warning. NEVER divide by zero.
       Required behavior, stated in SKILL.md's cluster-03 precondition."""

def belief_update(belief: dict, mdp: MDP, observation_model: Callable,
                  action, observation) -> dict:
    """b'(s') ∝ O(o|a,s') * sum_s T(s'|s,a) * b(s), then normalize.
       Post-condition: sum(b'.values()) == 1.0 within tolerance (INV-2)."""

def belief_greedy_action(mdp, U_belief_fn, belief): ...

def qmdp_value(mdp, U, belief) -> dict: ...
    """QMDP approximation for POMDP action selection."""

def monte_carlo_tree_search(mdp: MDP, s, simulations: int, depth: int,
                            c_uct: float = 1.0, seed: int | None = None): ...
    """Deterministic given `seed` — required for testability."""

def solve(contract: InputContract) -> OutputReport: ...
```

### 7.4 Sensitivity analysis (Output Contract field 5)

Every engine's `solve()` must populate `sensitivity`. Minimum required perturbations:

| Job | Perturb | By |
|---|---|---|
| Stopping | `n` | ±20% |
| Stopping | `recall_accept_prob` / `rejection_prob` | ±0.2 (clamped to [0,1]) |
| Stopping | `search_cost` | ±50% |
| Multiobjective | each `k_i` | ±0.1, renormalized |
| Multiobjective | `risk_attitude` | to NEUTRAL |
| Sequential | `gamma` | ±0.05 (clamped below 1.0) |
| Sequential | `prior_belief` | to uniform |

For each: re-run the engine, record whether the decision changed. Classify `fragility` as `critical` if the decision flips under a perturbation within stated uncertainty, `fragile` if it flips at the boundary, `robust` otherwise.

---

## 8. Stage 4 — Audit (`core/audit.py`)

Closes D-19, D-20, D-21. The seven invariants in `SKILL.md` map one-to-one onto implemented checks.

| ID | Invariant | Implementation | Failure condition |
|---|---|---|---|
| INV-1 | Assumption-set match | `check_assumption_set_match` | The dispatched constant's calibration record does not equal the elicited (horizon, information, recall, rejection, payoff) tuple |
| INV-2 | Normalization | `check_normalization` | Any probability/belief vector sums outside 1.0 ± tol; any v_i outside [0,1]; any v_i(worst) ≠ 0 or v_i(best) ≠ 1 |
| INV-3 | Independence verified | `check_independence_recorded` | Additive or multiplicative form used without a passing `IndependenceTest` for every pair involved |
| INV-4 | Bellman fixed point | `check_bellman_fixed_point` | `max_s abs(U(s) - max_a Q(s,a)) > tolerance`, **or** any residual ratio `res[i+1]/res[i] > gamma + tol`. Closes D-21 |
| INV-5 | Range-fixed weights | `check_weight_ranges` | A scaling constant lacks an attached `AttributeRange` |
| INV-6 | Finite expectation | `check_finite_expectation_audit` | A stopping rule was applied while `payoff_diverges` is True |
| INV-7 | Over-determination | `check_overdetermination_audit` | Equations ≤ free parameters, or a recorded inconsistency exceeds tolerance |

```python
def run_validation_invariants(job: Job, contract: InputContract,
                              decision: Any, artifacts: dict) -> AuditResult:
    """THE function referenced by SKILL.md's orchestration pseudocode. Closes D-19.
       `artifacts` carries engine internals the invariants need
       (residual_history, belief vectors, weight/range bindings, calibration record).
       Runs every applicable invariant. Returns AuditResult with per-invariant
       residuals. Never raises — reporting is dispatch's job."""
```

**Normative — INV-4 must use `gamma`.** The current `verify_bellman_residual` accepts `gamma` and ignores it. The replacement must assert the contraction property: residuals shrink by a factor no worse than γ per sweep. A residual that grows, or shrinks too slowly, is a failed contraction and must surface as a failure with the numeric ratio attached.

**Normative — audit is unconditional.** `dispatch` calls `run_validation_invariants` on every path. There is no flag that skips it.

---

## 9. Stage 5 — Reporting (`core/report.py`)

Closes D-22. `OutputReport.to_markdown()` must emit exactly these six sections, in order, always:

```markdown
## Decision
<decision, in plain language, plus the action to take>

## Formula
**<formula_name>** — <citation, e.g. "c01 §4.1">
<formula_latex>

## Numbers
| Quantity | Value |
|---|---|
| cutoff r* | 38 |
| P_n(r*) | 0.3710 |

## Locked assumptions
| Contract field | Value | Source |
|---|---|---|
| horizon | fixed_known, n=100 | elicited |
| information | ordinal | elicited |
| recall_allowed | False | elicited |
...
> This result is valid only under exactly these assumptions and does not transfer
> to any other assumption set.

## Sensitivity
| Assumption | Perturbation | Decision | Fragility |
|---|---|---|---|
| n | 100 -> 120 | r* = 45 | robust |

## Audit
| Invariant | Result | Residual |
|---|---|---|
| INV-1 assumption-set match | PASS | — |
| INV-2 normalization | PASS | 0.0 |
```

**Normative:** when `audit.passed` is False, `to_markdown()` must lead with a prominent failure banner naming the failed invariants and the remediation, and must **not** present the decision as actionable.

**Normative — the 37% rule.** Whenever the 1/e constant appears in any rendered output, the assumption set must be printed adjacent to it in the same sentence or table row. Implement as a rendering-layer guard, not as author discipline.

---

## 10. Orchestration

### 10.1 `core/dispatch.py`

```python
def dispatch(job: Job | str | None, contract: InputContract) -> OutputReport:
    """The single public entry point. Exact order, no shortcuts:

       1. job = job or classify_job(contract)          # Stage 1
       2. require_complete(contract)                    # Stage 1 -> ContractIncomplete
       3. verify_preconditions(contract)                # Stage 2 -> PreconditionViolation
       4. report = ENGINES[job].solve(contract)         # Stage 3
       5. report.audit = run_validation_invariants(...) # Stage 4 — unconditional
       6. if not report.audit.passed:
              raise AuditFailure(..., audit=report.audit)   # loop back to Stage 1
          return report                                 # Stage 5
    """
```

Steps 2 and 3 must precede step 4 unconditionally. Step 5 must run on every successful path. This ordering *is* the product design; encode it as a single function so it cannot drift.

### 10.2 `__init__.py` public API

Must export exactly the names `README.md` and `SKILL.md` advertise (closes D-23, D-24):

```python
from .core.contract import (InputContract, Job, Horizon, Information, Payoff,
                            RiskAttitude, AttributeRange, IndependenceTest)
from .core.report import OutputReport, AuditResult, InvariantResult, SensitivityEntry
from .core.errors import (DominantCircuitError, ContractIncomplete,
                          PreconditionViolation, NoOptimalStoppingRuleExists,
                          NonMarkovProcess, IndependenceNotVerified,
                          AuditFailure, UnclassifiedVariant, NotInCorpus)
from .core.dispatch import dispatch
from .core.elicit import missing_fields, next_question, classify_job, flip_test
from .core.verify import verify_preconditions
from .core.audit import run_validation_invariants
from .engines import stopping, multiobjective, sequential

__all__ = [...]  # all of the above
```

Backwards compatibility with `DominantCircuitEngine`, `solve_optimal_stopping`, and `solve_additive_utility` is **not** required. Remove them.

---

## 11. Corpus authoring

Closes D-01, D-02. **This is the highest-priority work in this document.** Until it is done, the host AI has no authoritative content for two of three job types and will fabricate citations.

Both new files must match `c01`'s established structure, which is the house style and is not negotiable:

1. `# Cluster NN: <Title>` and a **Source** line naming the book.
2. `## Scope` — one paragraph.
3. Numbered sections, each with: formal statement, LaTeX formula, worked numeric example, fenced-code pseudocode block with **Inputs / Output / Invariant** lines beneath it.
4. `## Compact Worked Algorithm` — a `classify_and_solve`-style dispatch pseudocode covering every documented variant.
5. `## Decision Table` — one row per assumption combination, with the rule and its constant.
6. `## Key Invariants` — numbered.
7. Explicit **Anti-pattern** callouts wherever a constant or form is commonly misapplied.

Every formula that Engine B or C implements must be traceable to a numbered section, because `OutputReport.citation` will reference it.

### 11.1 `c02-multiple-objectives.md`

**Source:** *Decisions with Multiple Objectives* (Keeney & Raiffa). Required sections:

1. **Scope and when this cluster applies** — a fixed set of alternatives, ≥2 competing attributes, certainty or uncertainty.
2. **Objective hierarchy construction** — attributes, proxy vs. direct, the completeness/non-redundancy/operability criteria for a good attribute set.
3. **Dominance screening** — definition, why it must run before elicitation.
4. **Preferential independence (certainty)** — formal definition; pairwise vs. mutual; **the flip test procedure in full detail**, since §5.1 of this spec implements it; the n=3 special case where pairwise implies mutual.
5. **The additive value function** — `v(x) = Σ λ_i v_i(x_i)`; conditions; assessment of component value functions; the midvalue-splitting technique.
6. **Utility independence (uncertainty)** — definition; how it differs from preferential independence.
7. **The multiplicative utility function** — `1 + k·u(x) = Π(1 + k·k_i·u_i(x_i))` with `1 + k = Π(1 + k·k_i)`; the sign/branch of `k` as a function of `Σk_i`; additive as the `k→0` limit. **Include a worked numeric example with the solved `k`**, which becomes a golden test value.
8. **Risk attitude assessment** — certainty equivalent, risk premium, the symmetric-lottery and fractile methods; constant/decreasing/increasing risk aversion; exponential utility form.
9. **Scaling-constant assessment** — the trade-off/indifference procedure; **the range-dependence warning**: `k_i` is meaningless without its assessed `[worst, best]` range; why "importance weight" is a category error.
10. **Consistency checking and the over-determination loop** — eliciting more equations than free parameters; what to do when responses conflict (surface and re-elicit, never average).
11. **Compact Worked Algorithm** — `classify_and_solve` covering certainty/uncertainty × additive/multiplicative.
12. **Decision Table** and **Key Invariants**.

Anti-patterns to call out explicitly: adopting additive form for convenience; treating `k_i` as importance; skipping dominance screening; averaging away inconsistent responses; transferring weights across different attribute ranges.

### 11.2 `c03-sequential-decisions.md`

**Source:** *Algorithms for Decision Making* (Kochenderfer, Wheeler et al.). Required sections:

1. **Scope** — action now affects future state; known or unknown dynamics; full or partial observability.
2. **The MDP tuple** `(S, A, T, R, γ)` — formal definition; the Markov property; **how to detect a violation and how to restore it by state augmentation** (spec §6 `check_markov` depends on this).
3. **Utility, return, and the discount factor** — finite-horizon sum vs. infinite-horizon discounted vs. average return; why `γ ∈ [0,1)` is required for convergence.
4. **The Bellman expectation and optimality equations** — `Q(s,a) = R(s,a) + γΣT(s'|s,a)U(s')`; `U*(s) = max_a Q(s,a)`.
5. **Value iteration** — algorithm, contraction-mapping argument, **the residual bound `‖U_{k+1} − U_k‖ ≤ γ‖U_k − U_{k−1}‖`** (this is INV-4's mathematical justification and must be stated formally here), convergence criterion.
6. **Policy iteration and policy evaluation** — including the linear-system formulation.
7. **Bayes' rule and belief representation** — `P(x|y) = P(y|x)P(x)/P(y)`; discrete belief vectors; **the zero-likelihood case and the required reset-to-uniform behavior**.
8. **POMDPs** — the `(S, A, O, T, R, O(·), γ)` tuple; belief-state MDP reformulation.
9. **The belief update** — `b'(s') ∝ O(o|a,s')·Σ_s T(s'|s,a)·b(s)`, with the normalization step written explicitly; a worked numeric example that becomes a golden test.
10. **Approximate/online methods** — QMDP, one-step lookahead, rollout, MCTS with UCT; the exploration constant; when each is appropriate given a compute budget.
11. **Model-free methods** — Q-learning, SARSA; exploration/exploitation; the ε-greedy and softmax policies.
12. **Compact Worked Algorithm** — dispatch on observability × known/unknown model × compute budget.
13. **Decision Table** and **Key Invariants**.

Anti-patterns: applying Bellman methods to non-Markov processes without augmentation; using `γ = 1` on an infinite horizon; dividing by zero on zero-likelihood evidence; reporting a value function that has not converged; treating a POMDP as an MDP by ignoring observation noise.

---

## 12. Corpus correction — `c01` §10 parking formula (D-03)

`c01` §10 currently states:

> \[ d^{*} = \left\lfloor \frac{-\log 2}{\log(1-p)} \right\rfloor \]

where `p` is the occupancy rate. **This is wrong as written**, and the section contradicts itself two lines later.

Evaluated as printed:

| occupancy `p` | `floor(-log2 / log(1-p))` |
|---|---|
| 0.50 | 1 |
| 0.85 | 0 |
| 0.90 | 0 |
| 0.95 | 0 |
| 0.99 | 0 |

It returns **0 for every realistic occupancy** and *decreases* as occupancy rises — the exact opposite of the invariant printed immediately below it ("higher occupancy rate → larger cutoff distance"). It also contradicts the section's own worked claim that moving from 90% to 95% roughly doubles the expected search length.

The derivation the section describes in prose is: each spot is independently occupied with probability `p`, so the probability that `d` consecutive spots are *all* occupied is `p^d`. Setting `p^d = 1/2` and solving gives the distance at which you have an even chance of having found a space:

> \[ d^{*} = \left\lfloor \frac{-\log 2}{\log p} \right\rfloor \]

Evaluated:

| occupancy `p` | corrected `d*` | exact |
|---|---|---|
| 0.50 | 1 | 1.00 |
| 0.85 | 4 | 4.27 |
| 0.90 | 6 | 6.58 |
| 0.95 | 13 | 13.51 |
| 0.99 | 68 | 68.97 |

The 0.90 → 0.95 ratio is **2.05** — reproducing the section's "roughly doubles" claim exactly, which the as-written formula cannot do.

**Required actions:**

1. Correct the formula in `c01` §10 to `d* = floor(-log 2 / log p)`.
2. Add the corrected worked table above to the section.
3. Implement `parking_cutoff` per §7.1 against the corrected form.
4. Add the regression test in §14.4 asserting monotonicity in `p` and the 0.90/0.95 doubling.
5. Before merging, check the formula against the source text in *Algorithms to Live By*, Chapter 1. If the book states it in terms of vacancy rate `(1−p)` rather than occupancy `p`, then the formula is right and the **variable naming** in `c01` is what is wrong — in that case, rename the parameter to `vacancy` throughout §10 and fix the invariant sentence instead. Either way the internal contradiction must be resolved and the test must pass.

---

## 13. Documentation and packaging corrections

### 13.1 `SKILL.md` (D-24)

- Replace the "Compact orchestration (Python-computable)" block with code that calls the **real** API from §10. Every referenced function must exist and be importable.
- Add, after the orchestration block, an explicit host-AI protocol:
  > Call `missing_fields(contract)` / `next_question(contract)` to drive elicitation. Do not compute mentally. Do not proceed while `ContractIncomplete` is raised. On `UnclassifiedVariant` or `NotInCorpus`, tell the user the corpus does not cover their assumption set — **do not improvise a constant**.
- Keep the 8-question Socratic loop; extend it to cover every field in `REQUIRED_FIELDS`, including `payoff_diverges` and `markov_verified`, which currently have no question.
- Verify both cluster links resolve once §11 is complete.

### 13.2 `AGENTS.md` (D-26)

- Correct the directory map to the actual §3 layout.
- Add a line stating that the library is non-interactive and that the host AI owns all conversation.
- Add: "If a required cluster file is absent, refuse the query and say so. Never answer from `SKILL.md`'s inlined formulas while citing a cluster section."

### 13.3 `README.md` (D-23)

- Fix the Usage block to the real API. Replace `InputContract(...)` with a complete, runnable example that fills a real contract and prints `report.to_markdown()`.
- Change "enforced in code" claims under Anti-Cargo-Cult Rules to reflect what is actually enforced, and cite the invariant ID (INV-1 … INV-7) for each.

### 13.4 `main.py` (D-25)

Rewrite as a non-blocking demonstration: build 2–3 fully-specified `InputContract` fixtures in code (one per job), call `dispatch`, print `to_markdown()`. Fix the import to `from dominant_circuit.engine …`. If an interactive mode is kept, gate it behind `--interactive` and `sys.stdin.isatty()`, and have it construct a contract and call the same `dispatch`. It must never be the only path to a result.

### 13.5 `pyproject.toml` (D-28, D-29)

- Remove `numpy`/`scipy` unless Engine C actually imports them (bisection in Engine B and value iteration in Engine C can be pure-Python; if `numpy` is used, keep it and drop `scipy`).
- Add the `src/dominant_circuit/py.typed` marker file the config already declares.
- Replace the `example.com` author email.
- Add `[tool.pytest.ini_options] addopts = "--cov=dominant_circuit --cov-fail-under=85"`.

---

## 14. Test suite

Closes D-27. `pytest`, in `tests/`. All values below were computed independently and are the acceptance oracle — **if the implementation disagrees with these numbers, the implementation is wrong.**

### 14.1 Exact finite-n optimal cutoff (`test_stopping.py`)

`optimal_cutoff(n)` must return exactly:

| n | r* | P_n(r*) |
|---|---|---|
| 1 | 1 | 1.000000 |
| 2 | 1 | 0.500000 |
| 3 | 2 | 0.500000 |
| 4 | 2 | 0.458333 |
| 5 | 3 | 0.433333 |
| 6 | 3 | 0.427778 |
| 7 | 3 | 0.414286 |
| 8 | 4 | 0.409821 |
| 9 | 4 | 0.405952 |
| 10 | 4 | 0.398690 |
| 100 | 38 | 0.371043 |
| 1000 | 369 | 0.368196 |

Tolerance 1e-6. Note that n=1…5 reproduce `c01` §4's small-n table, which is the cross-check that the formula is transcribed correctly.

**Required regression test (D-14):**
```python
def test_exact_beats_asymptotic_at_n100():
    assert optimal_cutoff(100)[0] == 38
    assert asymptotic_cutoff(100)[0] == 37     # round(100/e)
    # exact must be the default path
    assert dispatch(Job.STOPPING, classical_contract(n=100)).numeric["r_star"] == 38
```

**Convergence:** `abs(optimal_cutoff(n)[0]/n - 1/e) < 0.01` and `abs(P - 1/e) < 0.01` for n = 1000.

### 14.2 Threshold rule (`test_stopping.py`)

`threshold_percentile(k)`:

| k | t_k |
|---|---|
| 1 | 0.5033 |
| 2 | 0.6907 |
| 3 | 0.7762 |
| 4 | 0.8248 |
| 10 | 0.9240 |
| 50 | 0.9841 |

Tolerance 1e-4. These reproduce `c01` §6's stated 0.50 / 0.69 / 0.78. Assert monotonic increase in `k`, `t_0 == 0.0`, and that `threshold_rule` returns a numeric schedule, not prose (D-17).

### 14.3 Assumption-set lock (`test_stopping.py`) — closes D-15, D-16

```python
def test_recall_constant_locked_to_calibration():
    assert cutoff_with_recall(100, 0.5)[0] == 61
    with pytest.raises(UnclassifiedVariant):
        cutoff_with_recall(100, 0.3)      # 0.61 is NOT valid here

def test_rejection_constant_locked_to_calibration():
    assert cutoff_with_rejection(100, 0.5)[0] == 25
    with pytest.raises(UnclassifiedVariant):
        cutoff_with_rejection(100, 0.2)   # 0.25 is NOT valid here

def test_no_fallthrough_default():
    """An assumption combination absent from c01's Decision Table must raise,
       never silently return the 37% constant."""
    with pytest.raises(UnclassifiedVariant):
        select_stopping_rule(contract_with_recall_and_rejection_both_set())
```

### 14.4 Other Engine A rules (`test_stopping.py`)

| Function | Input | Expected |
|---|---|---|
| `cutoff_unknown_horizon_uniform` | n_max=1000 | r=135, success ≈ 0.2707 |
| `cutoff_stochastic_stop` | p=0.01 | r=18, success ≈ 0.236 |
| `cost_aware_threshold` | (0,1,c=0.02) | 0.8000 |
| `cost_aware_threshold` | (0,1,c=0.5) | 0.0 (accept first offer) |
| `cost_aware_threshold` | (100000,200000,c=0.02) | 180000.0 |
| `burglar_ceiling` | q=0.9, m=1.0 | 9.0 |
| `parking_cutoff` | 0.90 | 6 |
| `parking_cutoff` | 0.95 | 13 |
| `parking_cutoff` | 0.99 | 68 |

Plus (D-03), two monotonicity/doubling assertions. Note that the doubling claim must be tested on the **unfloored** quantity: `-log2/log(p)` gives 6.58 → 13.51 (ratio 2.05), whereas the floored integers give 6 → 13 (ratio 2.167). Expose the unfloored value as `parking_cutoff_exact(occupancy) -> float` for this purpose.

```python
def test_parking_monotonic_in_occupancy():
    ps = [0.5, 0.85, 0.9, 0.95, 0.99]
    ds = [parking_cutoff(p) for p in ps]
    assert ds == sorted(ds)                    # non-decreasing; as-written formula fails this
    assert all(d > 0 for d in ds)              # as-written formula returns 0 for p >= 0.75

def test_parking_doubling_claim():
    """c01 §10: 90% -> 95% roughly doubles the expected search length."""
    ratio = parking_cutoff_exact(0.95) / parking_cutoff_exact(0.90)
    assert abs(ratio - 2.0) < 0.15             # actual 2.054
```

### 14.5 Preconditions (`test_verify.py`)

```python
def test_diverging_payoff_blocks():            # D-08
    c = stopping_contract(); c.payoff_diverges = True
    with pytest.raises(NoOptimalStoppingRuleExists) as e:
        dispatch(Job.STOPPING, c)
    assert "Kelly" in e.value.remedy

def test_unelicited_divergence_is_not_assumed_false():   # the core of D-08
    c = stopping_contract(); c.payoff_diverges = None
    with pytest.raises(ContractIncomplete) as e:
        dispatch(Job.STOPPING, c)
    assert e.value.field == "payoff_diverges"

def test_non_markov_blocks():                  # D-09
    c = sequential_contract(); c.markov_verified = False
    with pytest.raises(NonMarkovProcess):
        dispatch(Job.SEQUENTIAL, c)

def test_independence_requires_recorded_test():          # D-07
    c = multiobjective_contract(); c.independence_tests = []
    with pytest.raises(IndependenceNotVerified):
        dispatch(Job.MULTIOBJECTIVE, c)

def test_bare_boolean_cannot_satisfy_independence():     # D-07, the sharp edge
    c = multiobjective_contract()
    with pytest.raises((TypeError, IndependenceNotVerified)):
        c.independence_tests = [True]; dispatch(Job.MULTIOBJECTIVE, c)

def test_weights_without_ranges_blocked():     # D-11
def test_underdetermined_elicitation_blocked():# D-10
def test_gamma_one_infinite_horizon_blocked(): # Bellman convergence
```

### 14.6 Engine B (`test_multiobjective.py`) — closes D-13

```python
def test_sum_one_routes_additive():
    r = solve_multiobjective(weights={"a":0.6,"b":0.4}, ...)
    assert r.formula_name == "Additive Value Function"
    assert abs(solve_k({"a":0.6,"b":0.4}, 1e-9)) < 1e-9

def test_sum_not_one_routes_multiplicative_not_error():
    """The current build RAISES here. It must ROUTE."""
    r = solve_multiobjective(weights={"a":0.6,"b":0.6}, ...)
    assert r.formula_name == "Multiplicative Utility Function"
    assert solve_k({"a":0.6,"b":0.6}, 1e-9) < 0        # sum > 1 -> -1 < k < 0

def test_k_branch_for_sum_less_than_one():
    assert solve_k({"a":0.3,"b":0.3}, 1e-9) > 0

def test_multiplicative_reduces_to_additive_as_k_to_zero(): ...
def test_dominance_screen_runs_before_elicitation(): ...
def test_normalization_endpoints():   # v_i(worst)==0, v_i(best)==1
```

The worked numeric example authored in `c02` §7 becomes an additional golden test.

### 14.7 Engine C (`test_sequential.py`) — closes D-12, D-21

Use a small, hand-solvable MDP (2–3 states, 2 actions) with an analytically known `U*`.

```python
def test_value_iteration_converges_to_known_optimum(): ...
def test_bellman_fixed_point_holds_after_convergence():
    """U(s) == max_a Q(s,a) within tolerance for all s."""
def test_residual_shrinks_by_gamma():          # INV-4, closes D-21
    _, residuals = value_iteration(mdp, k_max=100, tolerance=1e-9)
    for prev, cur in zip(residuals, residuals[1:]):
        assert cur <= gamma * prev + 1e-12
def test_audit_catches_non_contraction():
    """Feed a fabricated residual history that grows; INV-4 must FAIL."""
    res = run_validation_invariants(Job.SEQUENTIAL, contract, None,
                                    {"residual_history": [1.0, 2.0]})
    assert not res.passed
    assert any(r.invariant_id == "INV-4" for r in res.failures)
def test_belief_sums_to_one_after_update(): ...
def test_zero_likelihood_resets_to_uniform_not_zero_division():
    b = belief_update(belief, mdp, obs_model, action, impossible_observation)
    assert abs(sum(b.values()) - 1.0) < 1e-9
def test_mcts_deterministic_under_seed(): ...
```

### 14.8 Pipeline and reporting (`test_dispatch.py`) — closes D-19, D-20, D-22, D-23

```python
def test_readme_api_imports():                 # D-23
    from dominant_circuit import dispatch, InputContract   # must not raise

def test_skill_md_orchestration_symbols_exist():           # D-24
    """Every function named in SKILL.md's orchestration block is importable."""

def test_audit_runs_on_every_success_path():   # D-20
    r = dispatch(Job.STOPPING, complete_contract())
    assert r.audit is not None and len(r.audit.results) > 0

def test_failed_audit_raises_not_returns():    # D-20
def test_report_has_all_six_fields():          # D-22
    r = dispatch(Job.STOPPING, complete_contract())
    for f in ("decision","formula_name","numeric","assumptions","sensitivity","audit"):
        assert getattr(r, f) is not None
    assert len(r.sensitivity) >= 1
    assert "§" in r.citation

def test_37_percent_never_rendered_bare():     # the headline anti-cargo-cult rule
    md = dispatch(Job.STOPPING, classical_contract(n=1000)).to_markdown()
    if "37" in md or "0.368" in md:
        assert "ordinal" in md and "no recall" in md.lower()

def test_no_blocking_io_anywhere():            # D-04
    """Static check: `input(` appears nowhere under src/."""
```

### 14.9 Corpus integrity (`test_corpus.py`) — closes D-01, D-02

```python
def test_all_three_clusters_exist(): ...
def test_all_skill_md_links_resolve():
    """Parse every relative markdown link in SKILL.md; assert the file exists."""
def test_every_citation_resolves():
    """For each engine's citation strings ('c01 §4.1'), assert the cluster file
       exists and contains a heading matching that section number."""
def test_every_cluster_has_required_sections():
    """Scope, Compact Worked Algorithm, Decision Table, Key Invariants."""
```

---

## 15. Acceptance criteria — definition of done

The work is complete when all of the following hold:

1. All three cluster files exist; every link in `SKILL.md` resolves; every `citation` string emitted by any engine resolves to a real section (§14.9).
2. `from dominant_circuit import dispatch, InputContract` succeeds, and every symbol named in `SKILL.md`'s orchestration block is importable (§14.8).
3. `grep -rn "input(" src/` returns nothing.
4. All three engines return a complete six-field `OutputReport`.
5. Every defect D-01 … D-29 is closed, each with the test that proves it.
6. `pytest` passes with ≥85% line coverage on `src/dominant_circuit/`.
7. **The four product-intent tests in §1 pass**, specifically:
   - an incomplete contract cannot yield a number (`ContractIncomplete` names the missing field and supplies the question);
   - `payoff_diverges=True` yields `NoOptimalStoppingRuleExists`, never an answer;
   - changing `recall_accept_prob` from 0.5 to 0.3 changes the output (to a refusal), rather than silently reusing 0.61;
   - a failed invariant raises `AuditFailure` and is never buried inside a returned report.
8. `python main.py` runs to completion with no TTY and prints three complete reports.
9. `c01` §10 is corrected and the parking monotonicity test passes.
10. `README.md`, `AGENTS.md`, and `SKILL.md` describe only software that exists.

---

## 16. Suggested sequencing

Each milestone should be independently reviewable.

| # | Milestone | Closes | Notes |
|---|---|---|---|
| M1 | Author `c02` and `c03` | D-01, D-02 | **Blocks everything else.** Engines B and C cannot be specified against a corpus that does not exist. |
| M2 | Skeleton: `core/contract.py`, `errors.py`, `report.py`, empty `engines/`, `tests/` | D-22 (structure), D-26 | Establishes the types everything else depends on |
| M3 | `elicit.py` + `verify.py` + `dispatch.py` wired end-to-end, raising correctly with a stub engine | D-04…D-11, D-20 | The pipeline works before any math is correct |
| M4 | Engine A complete + `c01` §10 correction | D-03, D-14…D-18 | Largest math surface; corpus already exists |
| M5 | `audit.py`, all seven invariants | D-19, D-21 | Depends on M4 for real artifacts to audit |
| M6 | Engine B | D-13 | Depends on M1 |
| M7 | Engine C | D-12 | Depends on M1 |
| M8 | Sensitivity analysis across all engines | D-22 (field 5) | Needs all engines re-runnable |
| M9 | Docs, `main.py`, packaging, coverage gate | D-23…D-29 | Final pass |

---

## 17. Non-goals and constraints

- **No LLM calls from inside the library.** The package must have zero network dependencies and zero model dependencies. The host AI calls the library, never the reverse.
- **No conversational logic in Python.** Question wording lives in `QUESTION_BANK` and `SKILL.md` as data, not as control flow.
- **No new mathematics.** Every formula must trace to a numbered section of a cluster file, which traces to a cited source in `NOTICE.md`. If a user's problem is not covered, the correct behavior is `UnclassifiedVariant`, not invention. This constraint is the product.
- **No silent approximation.** Asymptotic shortcuts are opt-in via `exact_finite_n=False` and must be recorded in the audit with their exact-vs-approximate delta.
- **No web UI, no persistence, no async.** Out of scope for this version.
- **Backwards compatibility is not required.** `DominantCircuitEngine` and the current `solve_*` functions may be deleted outright.

---

## Appendix A — Verification method for the numbers in this document

Every golden value in §14 was computed directly from the formulas in `c01`, not copied from prose:

- **§14.1** — brute-force argmax of `P_n(r) = ((r−1)/n)·Σ_{j=r}^{n} 1/(j−1)` over all r ∈ [1,n], per `c01` §4.1. Cross-checked against `c01` §4's small-n table for n = 1…5: agreement on all five rows.
- **§14.2** — direct evaluation of `t_k = 1/(1 + 0.804/k + 0.183/k²)`, per `c01` §6. Cross-checked against the book's worked values 0.50 / 0.69 / 0.78: agreement to two decimals.
- **§14.4 cost-aware** — `p* = 1 − √(2c)`, per `c01` §9. Cross-checked against §9's stated behavioral consequence that `c ≥ 0.5` collapses the threshold to the bottom of the range: confirmed, `p*(0.5) = 0`.
- **§14.4 parking** — both the as-written and corrected forms evaluated across p ∈ {0.5, 0.85, 0.9, 0.95, 0.99}; see §12. The corrected form reproduces `c01` §10's own "90% → 95% roughly doubles" claim (ratio 2.05); the as-written form returns 0 throughout and cannot.
- **§14.8 off-by-one** — `round(100/e) = 37` versus exact argmax `r*(100) = 38`, confirming that the asymptotic shortcut is not merely imprecise but returns a different integer at a scale users will plausibly supply.

The engineer should re-derive these independently before treating them as authoritative.
