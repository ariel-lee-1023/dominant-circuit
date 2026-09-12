# Engineering remediation: schema 2, version 0.5

Implementation base: `ac9e2ccec4290c37e19009a6aa2e1eb89a1cf537`.
Reviewed worklist baseline: `b0fdf0a8644799b987ae0564febb85f75ea67f58`.
Implementation owner: Codex. Release approval belongs to the repository maintainer;
independent model review and live-host evaluation are pending, not signed off here.

## Baseline reconciliation and reproduction

The current branch had 170 passing tests and no existing expected failures. Fixtures
A, B and D reproduced the misleading semantics. Fixture C reproduced the reversal and
showed missing margin and boundary reporting. All four new regressions initially failed.
The baseline had already removed `stage0/` and its tests. The original remediation updates
`SKILL.md` and introduces a typed description interface instead of restoring that removed
philosophical prerequisite. No source corpus or public API symbol was removed.

Final deterministic verification: 210 passed, 0 failed; 92.21% coverage. Fatal lint,
whitespace checks, the original demo and reflective example pass.

Environment: Python 3.12.7, pytest 7.4.4. The default Python 3.13 interpreter had no
pytest. Network installation was unavailable, so verification used an isolated temporary
venv with the existing Python 3.12 site packages and an offline editable install:

```bash
python -m venv --system-site-packages /tmp/dc-env
/tmp/dc-env/bin/python -m pip install --no-build-isolation --no-deps -e .
/tmp/dc-env/bin/python -m pytest tests/test_remediation.py -q --no-cov
/tmp/dc-env/bin/python -m pytest
/tmp/dc-env/bin/python examples/reflective_decision.py
/tmp/dc-env/bin/python scripts/check_release.py
```

The release gate intentionally fails until independent review and live-host evidence
are recorded in `docs/release-evidence.json`. A passing deterministic suite is not a
substitute for that evidence. No live model was run and no deployment was performed.

## Work item evidence

| Item | Implementation and evidence | Boundary or remaining release work |
|---|---|---|
| DC-00 | Current commit reconciled; original 170 tests pass before changes; fixtures A-D fail before fixes | Baseline and environment recorded above |
| DC-01 | Structured `ValueIterationResult`; true residual, returned-value greedy policy, numerical termination, finite-model validation | Floating point computation; no exact policy-optimality claim |
| DC-02 | Rule-dependent completeness and calibration retain unknown recall/rejection; explicit scenarios | Missing inputs raise `ContractIncomplete` with field and remedy |
| DC-03 | Explicit outcomes and per-probe execution; separate model, action and feasibility comparisons | Full-policy scope for sequential probes; finite probes do not justify dropping a factor |
| DC-04 | Audit manifests, missing-check coverage, consistent readiness rendering, deprecated completion semantics | INV-7 is advisory; failed mandatory audit still raises |
| DC-05 | Description, translation records, capability registry, explicit unsupported-model result | Host supplies interpretations; no prose classifier or arbitrary solver composition |
| DC-06 | Origin and acceptance axes, dependency references, tagged serialization, branch scoping, revision history | Host owns evidence retention and event authenticity |
| DC-07 | Separate computation/support/readiness, reasons, conditions and reopening triggers | Point weights can be irrelevant within an adopted certified domain; other unresolved prerequisites remain conditional |
| DC-08 | Probability, reward, state, range, score and terminal checks; impossible evidence rejected | Static belief estimation only; finite-horizon and dynamic filtering requests are unsupported |
| DC-09 | Winner, runner-up, margin, ties, switching boundary and joint box-simplex optimization | Arbitrary extra linear relationships and nonlinear domains report unsupported coverage; no unadopted regret rule |
| DC-10 | Exploratory, decision-specific, standing and suspended preference revisions; bounded-weight exploration | Partial rankings are retained as preference data; no invented point-ranking solver |
| DC-11 | Explicit scoped predicates evaluated before ranking, unknown feasibility, bounded threshold checks | Constraint predicates currently apply to static alternatives; no automatic relaxation |
| DC-12 | Stateful adapter tests, paraphrase/fact-change tests, six live-host case specifications and burden metrics | Actual repeated live-host runs and independent usefulness review remain pending |
| DC-13 | Schema/API migration, current host docs, executable reflective example and release gate | No release approval claimed; complete external evidence before publishing |

Regression coverage is in `tests/test_remediation.py` and `tests/test_evidence_pipeline.py`.
Existing tests were migrated where they explicitly required vacuous audits, uniform resets,
unconditional execution language, implicit assumptions or unsupported stability claims.
These compatibility changes are intentional, not waived correctness requirements.

## Numerical semantics

`value_iteration` returns `ValueIterationResult`. Three-way unpacking remains supported:
`values, policy, iterate_differences = value_iteration(...)`. The third legacy element
contains successive-iterate differences, not Bellman residuals.

Schema 2's public `tolerance` is an absolute returned-value Bellman-residual tolerance.
Earlier versions used a successive-iterate difference with the same parameter name.
The change is explicit in version 0.5; iteration counts can differ. `k_max` must be a
positive integer, tolerance finite and positive, and `0 <= gamma < 1`.

Termination is `converged`, `budget_exhausted` or `numerical_failure`. Invalid inputs
raise `PreconditionViolation` before iteration. A budget-limited computation retains
its diagnostic result and is never relabelled converged. Terminal states are explicitly
zero-reward absorbing states; contradictory supplied rows are rejected. Other state/action
pairs need complete rewards and normalized transitions. Callable models must be pure,
accept `(state, action)` and return finite rewards or probability dictionaries.

For a finite bounded discounted MDP, Bellman's contraction gives
`||V - V*|| <= ||V - T(V)|| + gamma ||V - V*||`, hence the reported value-error bound
`r/(1-gamma)`. Here `r = max_s |T(V)(s)-V(s)|` is computed on returned values. The
policy is recomputed greedily against those same values. The contraction background is
in [MIT's Bellman and value-iteration notes](https://gradml.mit.edu/reinforcement/value_bellman/).
The residual-bound derivation above is the implementation's application of that result.
The bound concerns values, not a separate exact action certificate; floating-point
roundoff is not enclosed by interval arithmetic.

## Readiness and audit semantics

| State | Meaning |
|---|---|
| `exploratory` | Proposed or scenario-only consequential inputs are in use |
| `conditional` | Useful computation exists, but support, feasibility or uncertainty treatment remains unresolved |
| `ready_under_stated_conditions` | Supported model, computational evidence, scoped accepted inputs, feasibility and uncertainty treatment meet the policy |
| `blocked` | Failed mandatory checks, numerical failure, or no known-feasible recommendation |

Readiness is versioned and carries supporting IDs, reasons, remaining uncertainty,
conditions, next observations, completed checks and reopening triggers. An accepted
residual-uncertainty treatment is a scoped choice, not a claim that uncertainty vanished.
An explicitly adopted weight region can establish that unresolved point weights do not
change the action, avoiding an unnecessary point-weight question.

Required manifests are `INV-1, INV-6` for stopping; `INV-3, INV-5` for comparisons;
`INV-4, INV-markov` for MDP computations; and `INV-2` for static belief estimation.
`AuditResult` exposes required IDs, completed results, failures, missing checks and
justified not-applicable entries. An empty audit fails. `INV-7` remains visible but
advisory. Recorded Markov or independence booleans are assumptions; their empirical
support is assessed separately through provenance.

`analysis_is_complete` is deprecated. Its compatibility value can be true only for
scoped ready results with passing mandatory checks. It never means that additional
deliberation cannot help. `execution_note` describes readiness and separate execution
authority. Markdown uses a Readiness section. Conditional action summaries avoid
imperative execution instructions. A recommendation is never authorization to act.

Dispatch raises for invalid, missing, unsupported or mandatory-audit-failed contracts.
Use `translate_decision` for a structured unsupported or unresolved translation result.
Useful budget-limited, scenario, preference-sensitive and infeasible comparison results
are retained with readiness reasons. Direct engine calls do not establish readiness;
use public `dispatch` for the full policy.

## Data, provenance and migration

`DecisionDescription` retains ID/revision, question, options/actions, information types,
objectives, temporal structure, uncertainty, constraints and unresolved interpretations.
Each `TranslationRecord` names source IDs, target field, interpretation, rule and
unresolved alternatives. Field interpretations are provided by the host. Negotiation,
feedback-loop shape or accumulation never silently chooses an information type,
objective or horizon. Static comparisons take a direct route.

`ConsequentialInput` separates origins (`user_report`, `measurement`, `external_source`,
`model_proposal`, `derived`, `legacy`) from acceptance (`unresolved`,
`accepted_for_this_decision`, `scenario_only`, `rejected`). It retains evidence reference,
scope, revision, uncertainty, timestamp, alternatives and dependency IDs. Adopted use
requires an identifiable host event. References must resolve within the authorized host;
the deterministic library does not authenticate them or copy entire conversations.
Export retains references; the host must retain the referenced evidence for as long as
its reports remain auditable and must mark a record unresolved if evidence is removed.

Use `encode`/`decode` for lossless JSON-compatible archival records, including enums,
tuple dictionary keys, false, zero, indifference, null and not-applicable labels.
Callable models cannot be serialized: supply tables for portable records. `to_dict`
is presentation JSON; non-string keys are displayed as strings and nonfinite diagnostic
numbers as null. Use tagged archival encoding when key identity matters.

`migrate_legacy_contract` loads plain historical mappings with `legacy` origin and
`unresolved` acceptance. It does not invent historical adoption. `decode` marks loaded
reports conditional for current use. `load_historical_report` preserves the original
artifact while explicitly invalidating the old execution verdict.

`scenario_branch` copies a contract, increments its revision and gives overridden inputs
proposed, scenario-only provenance. `DecisionSession.revise` retains history and invalidates
transitively dependent outputs, leaving unrelated outputs available. Derived inputs become
unresolved until recomputed. Hosts must drive revisions through this interface and track
output dependencies; mutating a detached historical Python object cannot notify a session.

## Robustness and preference boundaries

`OverturnResult.overturns` is a compatibility boolean for a demonstrated action or
feasibility change. Inspect `outcome` and the probe records instead. No completed probe,
or incomplete/unsupported coverage, yields `untested`. `is_small_quantity` is deprecated
and always false. `elicitation_plan.droppable` remains empty for finite screening.
Model changes are separate from action changes. MDP comparisons cover the full policy;
belief-estimation reports do not claim to compare planned actions.

`WeightRegion` supports lower/upper weight bounds plus `sum(weights)=1`, fixed recorded
attribute ranges, source, scope and acceptance. It rejects empty regions and changed
assessment ranges. Arbitrary additional relationships are reported as unsupported.
For a linear pairwise score difference, assigning lower bounds and then filling the
lowest coefficients first solves this restricted linear program over the whole domain.
Every certificate includes the minimizing witness and minimum margin. This is joint
optimization, not one-at-a-time sampling. Two-attribute switching boundaries are analytic.
Ties use an absolute `1e-9` tolerance. Margins and robustness include dominated candidates
so zero-weight ties and the true runner-up are not hidden by presentation screening.
`explore_weight_region` labels its computational anchor as a scenario; its whole-domain
claim derives from optimization, not from adoption of the anchor.

Constraints use `<=`, `>=`, `==` or membership predicates, each with scope and provenance.
Missing values produce unknown feasibility. Threshold constraints also accept sourced
`{lower, upper, evidence_ref}` intervals: both endpoints must give the same result to
establish known feasibility throughout the interval. Other uncertain predicates remain
unknown. Violated or unknown options cannot silently win a feasible ranking.

## Interaction release gate

`tests/fixtures/host_release_cases.json` specifies allowed outcomes and forbidden
transitions for six critical multi-turn cases. Deterministic tests assert observable
state, provenance, feasibility and reopening invariants. They also test wording changes
that should not change already-structured inputs, and factual changes that should.
They do not prove that an arbitrary conversational model translates language correctly.

Before publishing, run each live-host case three times with the candidate host prompt,
model/version and tool configuration recorded. Retain structured states, final reports,
failure traces, unnecessary-question counts and useful-recovery scores. Human review
must assess interpretation, usefulness and interaction burden separately from forbidden
transitions. `scripts/check_release.py` requires the recorded evidence and independent
review. Report the denominator and observed failures; zero observed failures is not a
universal guarantee. See `docs/release-evidence.json` for current gate status.


## Stage 0 follow-up

The subsequent [Stage 0 implementation](STAGE0.md) restores the optional investigation
skill with an evidence-return cycle, shared provenance and bound solver handoffs. Its
[release record](STAGE0-RELEASE.md) supplements this backlog. It restores and rewrites
the four historical conceptual notes to remove conflicting operational claims; the
three authoritative solver clusters remain unchanged by that follow-up.
