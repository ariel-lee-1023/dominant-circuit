---
name: stage0-structure-first
description: "Stage 0 for dominant-circuit, distilled from 3 sources: Meadows Thinking in Systems, Pearl & Mackenzie The Book of Why, Page The Model Thinker. Given an unshaped situation, installs an explicit starting model — names its stocks/flows/loops, its DAG and what that DAG makes identifiable, and its equilibrium/cycle/randomness/complexity class — and emits six required fields: starting model, observation instruction, commitments, prohibitions, overturn conditions, rival models. Then either hands off the four classifying InputContract fields to dominant-circuit or refuses a specific over-reaching claim. Never outputs a decision, a number, or prose insight. Use before any decision solver runs, whenever a case has not yet been reduced to job/horizon/information/payoff."
---

# Stage 0 — Structure First

**Books**: 3 | **Depth**: reference | **Citation anchors**: `§N` (top-level), `§N.M` (framework blocks)

Cite as `meadows §2.4`, `pearl §2.6`, `page §2.3` — every numbered heading in the three reference
files is a stable anchor. Do not cite by heading text; text gets rewritten, numbers do not.

---

## 1. Why this stage exists

**There is always a model before there can be observation.** Without one, a person does not know
where to look, and data does not volunteer what causes what.

This is not a methodological sentiment. Each of the three books states it as a hard constraint:

- **Pearl** — "no causes in, no causes out." A causal model is separate from, and *prior to*, any
  data. Probability lives on rung 1 of the Ladder of Causation and no quantity of data climbs to
  rung 2 (`pearl §2.1`).
- **Meadows** — the system boundary is a **modeling choice**, not a fact discovered in the world:
  "the world is a continuum. Where to draw a boundary depends on the purpose of the discussion"
  (`meadows §2.4`).
- **Page** — the model class decides what counts as a variable and what shape the answer can take;
  committing to a class commits you to a result type (`page §2.3`).

Therefore prejudgment is unavoidable. The only real choice is **deliberate prejudgment or
unexamined prejudgment.** Stage 0's job:

> Install a deliberate starting model so the user knows where to look — and put what that model
> commits to, what it forbids, and what would overturn it, on the table where it can be audited.

## 2. What this is, and what it is not

This is **not** a decision solver. `dominant-circuit` is the solver; it is good, but it assumes
job / horizon / information / payoff are already filled in, after which the answer is close to
unique. Stage 0 is everything **before** that.

A correct Stage 0 output is **the six fields of §6** — never an answer, never a ranked list of
options, never an essay. If it reads like commentary, it has failed.

Stage 0 also does not estimate. No effect sizes, no probabilities, no point estimates, no prices,
no retention numbers. Identifiability judgments and structural classification, and there it stops.

## 3. Default posture: commit a model, do not refuse

`dominant-circuit` runs on "refusal is the product," and it is right to: a user asking for a number
who receives a wrong number will act on it.

**That default is inverted here, and inverting it is the single easiest way to ruin this stage.**
A user arrives at Stage 0 *because* they have no boundary and no named structure. Answering
"boundary undeclared, cannot proceed" refuses to perform the one job this stage has.

| | `dominant-circuit` | Stage 0 |
|---|---|---|
| What the user wants | a number | a direction to look |
| Cost of a wrong output | acted on as if true — harmful | low: it is explicit, so observation corrects it |
| Cost of no output | low: user finds another route | **high: user keeps looking with an unexamined model** |
| Therefore default to | **refusing** | **committing to a model** |

A wrong model written down explicitly is *useful* — it is falsifiable and reality will correct it.
No model is *useless* — without one you cannot even tell which data to collect.

The refusals that survive here (§7.1) refuse a **claim the user asserted**, not the request for
help. `NotIdentifiable` rejects "this quantity is computable from that graph"; the graph is still
delivered, together with what would make the quantity identifiable.

## 4. Which book for which job (fixed order, not parallel)

Three organs of one judgment, applied in this order, because each stage's output is the next
stage's required input: **what can be seen → what can be claimed → what shape the answer can take.**

| Order | Book (→ file) | Question it answers | What it hands on |
|---|---|---|---|
| 1 | Meadows, *Thinking in Systems* → [references/reference-meadows-thinking-in-systems.md](references/reference-meadows-thinking-in-systems.md) | Where is the boundary? What accumulates vs. flows? Where are the loops, what polarity, how long the delays? | Nouns: stocks, flows, loops + polarity, delays, boundary |
| 2 | Pearl & Mackenzie, *The Book of Why* → [references/reference-pearl-book-of-why.md](references/reference-pearl-book-of-why.md) | Which arrow am I licensed to claim? Where does an intervention land? Is the target quantity identifiable? | Licence: DAG, mediator/confounder/collider, identifiability verdict |
| 3 | Page, *The Model Thinker* → [references/reference-page-model-thinker.md](references/reference-page-model-thinker.md) | Which model class is this? Equilibrium, cycle, randomness or complexity? Stable? | Shape: model class, result-type verdict, stability verdict, rival classes |

Pearl is the **only** source here with a mathematically hard definition of "mediator"
(chain / fork / collider, back-door, do-calculus). When a case turns on that classification, Pearl
is the sole authority — do not substitute intuition from the other two books.

## 5. The six capabilities, in fixed order

### 5.1 Domain triage (three questions, read-only)
Answer only from what the user has **already stated**; never infer from wording or tone.

1. Is the ask "which option do I pick" (decision) or "where would changing something change the
   outcome" (intervention)? → **decision vs. intervention**
2. Does any quantity accumulate over time — a level that persists between observations?
   → **dynamics vs. static**
3. Can the actor act on the system, or only observe it? → **rung 2 vs. rung 1** (`pearl §2.1`)

**Precedence rule.** These three questions never terminate in a refusal. If nothing has a boundary
and nothing accumulates and the ask is for commentary rather than structure, that is
`NotAStructuredProblem` — a *routing* verdict (this is a static one-shot decision, or it is not a
structural question at all), not a door closing. `NotAStructuredProblem` is checked **before**
`BoundaryFork`, and only one of the two ever fires.

### 5.2 Construct proposal (Meadows primary, Pearl secondary)
Name the stocks / flows / loops with polarity, and — wherever an intervention or a "what if we do X"
claim is present — the DAG nodes and edges.

- Every named stock carries a **unit**, and that unit must equal some flow's unit × time
  (`meadows §2.1`). This dimensional check is the only free mechanical self-audit available at this
  layer; run it before accepting any construct. If it fails, the construct is misnamed — not the check.
- **Provenance is mandatory.** Mark every construct as either *stated by the user* or *added by
  Stage 0*. An added construct is a proposal the user may reject; an unmarked added construct is
  the AI's opinion wearing the user's name.
- If constructs cannot yet be named, that is `ConstructProposal` (§7.2), not a stop.

### 5.3 Identifiability verdict (Pearl only)
Given the DAG and the observable set: is the target quantity identifiable? Apply the
confounder / mediator / collider test (`pearl §2.3`, `§2.4`) and the back-door / front-door criteria
(`pearl §2.5`, `§2.6`). If not identifiable, name **the specific thing that would fix it** — an
instrument, a front-door mediator, an added measurement, an RCT — never "insufficient data."

The DAG is **supplied by the user**. This stage can never verify that it is true, only what is
identifiable under it. So `assumption_provenance` is printed, always, not optionally.

### 5.4 Result-shape and stability verdict (Page only)
Classify long-run behaviour as **equilibrium / cycle / randomness / complexity** (`page §2.3`).

To assert equilibrium, either construct a Lyapunov function — bounded below, and strictly
decreasing by at least some A > 0 at every non-equilibrium step (`page §2.4`) — or verify all four
Markov conditions: finite states, fixed transition rule, ergodicity, non-cyclic (`page §2.5`).

Failing to construct a Lyapunov function is **not** proof of non-equilibrium (Collatz: converges in
every tested case, no Lyapunov function ever proven). Report **unresolved**, not "no equilibrium,"
unless the four Markov conditions have also been checked and fail.

If a quantity's distribution is power-law with tail exponent a ≤ 2, its mean does not converge
(`page §2.6`) — any downstream claim resting on "the average" is unsupported until the tail is checked.

### 5.5 Rival models (Page)
Before emitting, ask whether more than one structurally distinct model class is independently
plausible. If so, list them side by side **with the observation that would discriminate between
them**. Multi-model plurality is a legitimate terminal verdict, not a failure to try harder
(Lo's 21-model crisis analysis, Allison's three-model Cuban Missile Crisis — `page §2.2`).

Plurality is never an excuse to hand back nothing: rivals plus a discriminating observation *is* a
direction to look, and is frequently the most valuable output this stage produces.

### 5.6 Emit the six fields, then hand off or refuse
Emit §6 in full. Then either hand off the four classifying fields (§9) or refuse a specific
over-reaching claim (§7.1). Never both, never neither.

## 6. Output contract — six fields, all required

1. **Starting model** — variables, boundary, arrows, or stocks/flows/loops. Concrete enough to draw.
2. **Observation instruction** — given this model, where to look and what to measure next.
   **This is what the user actually came for, and it is the one field that may never be omitted.**
3. **Commitments** — what adopting this starting point commits you to: which variables are
   endogenous, which arrows are asserted to exist.
4. **Prohibitions** — what it forbids: which variable must not be conditioned on, which questions
   cannot be asked under this boundary, which quantities are unidentifiable under this graph.
5. **Overturn conditions** — what observation would replace this starting point with another.
6. **Rival models** — which other starting points are equally defensible, and what observation
   distinguishes them.

Fields 3 and 4 are the whole technical content of "deliberate prejudgment": **the cost of the
prejudgment must be settleable.**

## 7. Verdict taxonomy

Twelve verdicts in three classes. The class determines the posture, and the classes were previously
conflated — six of these are genuine refusals, three are forks that must never terminate the stage,
and three are findings that terminate only with a stated measurement that would resolve them.

### 7.1 True refusals (6) — refusing a claim the user asserted

| Verdict | Grounded in | Fires when |
|---|---|---|
| **CausalClaimFromObservationalOnly** | `pearl §2.1` | A rung-2/3 claim is asserted on rung-1 evidence only. |
| **ConditioningOnCollider** | `pearl §2.3`, `§2.9` | The case conditions on — or implicitly selects on — a common effect of two variables: self-selection, survivorship, M-bias. |
| **NotIdentifiable** | `pearl §2.7` | Under the user's own graph and observable set, repeated do-calculus cannot eliminate every do(·) term. Deliver the graph anyway; name what restores identifiability. |
| **UnobservedConfounder** | `pearl §2.5`, `§2.6` | A common cause of treatment and outcome is unobserved, no valid back-door set exists, and no mediator satisfies the front-door shielding condition. |
| **DimensionalMismatch** | `meadows §2.1` | A named "stock" fails unit = flow-unit × time. |
| **UnstableFixedPoint** | `page §2.4` | A fixed point exists but is not attracting — distinct from no equilibrium; something was found, it is just not where the system rests. |

### 7.2 Forks (3) — never terminal; these are the stage doing its job

| Verdict | Grounded in | Emit instead |
|---|---|---|
| **BoundaryFork** | `meadows §2.4` | 2–3 candidate boundaries, each with what it makes exogenous and therefore what it forbids you to ask. |
| **ConstructProposal** | `meadows §2.1`, `§2.2` | Candidate stocks / flows / loops as a marked proposal — user-stated vs. Stage-0-added flagged separately. |
| **RivalModels** | `page §2.2` | Competing model classes with their conflicting conclusions, plus the observation that discriminates. |

### 7.3 Conditional findings (3) — terminal only with a resolving measurement attached

| Verdict | Grounded in | Fires when |
|---|---|---|
| **LoopDominanceUndetermined** | `meadows §2.2` | Opposite-polarity loops present, current dominance not determinable from stated information. Never guess a lever direction — leverage intuition is famously wrong-signed (`meadows §2.5`). |
| **NoEquilibriumExists** | `page §2.4`, `§2.6` | No fixed point, no simple cycle, Lyapunov and Markov tests both fail — or the tail is power-law with undefined mean. Report this rather than manufacturing a settled number. |
| **NotAStructuredProblem** | `meadows §2.4` | No boundary, nothing accumulating, and the ask is commentary. A routing verdict: static one-shot decision, or out of scope. Checked before `BoundaryFork` (§5.1). |

Each §7.3 verdict must state what measurement would settle it. "Undetermined" without that is
indistinguishable from not having looked.

## 8. Mapping onto dominant-circuit's report structure

No new report model is needed. The existing five-part structure carries over intact, with the
zero-order term changing from *a number* to *a model*:

| Report part | In Stage 0 |
|---|---|
| `zero_order` | **the starting model** — the load-bearing trunk |
| `corrections` | factors that refine it without replacing it |
| `overturns` | **rival models** — a different trunk, not a bigger or smaller one |
| `dropped` | details the user raised that cannot change where to look |
| `hard_constraints` | the §7.1 refusals |
| `analysis_is_complete` | "stop reasoning, start observing" — the model is installed; remaining risk is factual, not analytical |

The overturn test carries over with sharper meaning here: **a factor that cannot change where to
look does not deserve the user's attention.**

## 9. Handoff — what Stage 0 fills in, and what it must not

Stage 0 emits **no numbers**, so it fills only the four classifying fields of `InputContract`:

| Field | Filled from |
|---|---|
| `job` | §5.1 question 1 + §5.4 result shape |
| `horizon` | §5.1 question 2 (accumulation present → not a one-shot) |
| `information` | §5.1 question 3 (observe-only vs. act) |
| `payoff` | §5.4 result-shape verdict |

Every numeric field (`n`, `gamma`, `scores`, `search_cost`, `transition`, `reward`, …) is left
`None` and **named in the observation instruction** as something the host must elicit. Filling a
numeric field here would smuggle an unelicited assumption past the very check this repository
exists to enforce.

Hand off only when all four classify. Otherwise emit §6 and the applicable §7 verdict, and say
plainly that the case is not yet reduced to a solver input.

## 10. Cross-book topic index

Terms appearing in two or more books.

- **Boundary / scope of object** → meadows `§2.4`, page `§2.2` (granularity is a scope choice)
- **Delay / lag / temporal structure** → meadows `§2.3`, page `§2.5`, `§2.7`
- **Feedback loop (reinforcing / balancing)** → meadows `§2.2`, page `§2.7`
- **Graph / structure representation** → pearl `§2.3`, meadows `§2.2`, page `§2.3`
- **History matters / does not matter** → meadows `§2.3`, page `§2.5`, `§2.7`
- **Identifiability / can this be known at all** → pearl `§2.7`, page `§2.4`
- **Intervention (do vs. observe)** → pearl `§2.2`, meadows `§2.5`
- **Mediator** → pearl `§2.4`, `§2.10` — **single source and sole authority**; neither other book has a rigorous mediator test
- **Multiple / conflicting explanations** → page `§2.2`, meadows `§2.6`
- **Stability / equilibrium** → page `§2.4`, `§2.5`, meadows `§2.2`

## 11. Scope, limits, provenance

Structural judgment only, from these three sources.

- **Pearl** supports identifiability and mediator / confounder / collider judgment but explicitly
  **not** numeric effect-size estimation (see the NOTICE in its reference file). A request for a
  point estimate or standard error routes to *Causality* (2009) or *Causal Inference in Statistics:
  A Primer* — never answered from here.
- **Page** supports model-class and result-type judgment, not the mechanics of any one of the
  book's ~30 individual models. Routing to a specific model's derivation is out of scope.
- **Meadows** leverage points at the rules / self-organization / goals / paradigms end are **not
  computable**; they are reported as hard constraints, not ranked. Only parameters, buffers,
  physical structure and delays admit sensitivity ranking, and even then Stage 0 names the
  structure and never the direction to push (`meadows §2.5`).
- **This stage never selects the model for the user.** It may propose, order, and price the
  alternatives. It may not silently pick one. The user owns the goal, and owns the starting point.
- For a topic none of the three books addresses, say so rather than inventing a verdict.
- **Depth note.** These reference files were distilled at `reference` depth: dense on decision
  criteria, without worked end-to-end examples. Anything presented as a worked example downstream
  is constructed, not quoted, and must be labelled as such.
