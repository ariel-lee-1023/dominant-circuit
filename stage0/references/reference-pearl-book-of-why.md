# The Book of Why: The New Science of Cause and Effect — Judea Pearl, Dana Mackenzie

**Format**: epub | **Pages**: ~400 | **Depth**: reference | **Anchors**: `§N`, `§N.M`

> **NOTICE — honest boundary of this source.** This is a popular narrative book. It gives the
> intuitive statements and worked cases for the Ladder of Causation, DAGs, d-separation, the
> back-door and front-door criteria, and do-calculus — but it does **not** contain theorem-level
> statements with proofs. Those live in Pearl's *Causality* (2009) and *Causal Inference in
> Statistics: A Primer*. Judgment: this source is sufficient to build a **structure adjudicator** —
> deciding which quantity is identifiable, where a mediator / confounder / collider sits, what must
> be adjusted for — but **not** sufficient to build an **estimation engine** that computes numeric
> causal effect sizes. Any request for a point estimate, standard error or effect-size number is
> declined and routed to *Causality* / *Primer*, never answered from this file.
>
> **Provenance of the formal statements below.** `§2.7` states do-calculus Rules 1–3 and cites the
> completeness theorem. These are **transcribed from this book's own informal presentation**, not
> from the primary theorem statements. They are precise enough to decide identifiability and to
> justify a `NotIdentifiable` verdict; they are **not** a substitute for the primary text, and any
> citation of them downstream must carry this note. A reference that looks checkable but cannot be
> checked against its stated source is the failure mode this provenance line exists to prevent.

> **Role in Stage 0 — the licence supplier.** Meadows says what there is to look at; Pearl says what
> may be *claimed* about it. Pearl also supplies the strongest form of Stage 0's founding argument:
> a causal model is separate from, and prior to, the data — "no causes in, no causes out" (`§2.1`).
> Once a graph is committed to, this book says what becomes checkable (identifiability) and what
> becomes forbidden (conditioning on a collider). That pair *is* the price list of a deliberate
> prior commitment.

## 1. Mental Model (read first)

Probability alone lives on the first rung of a three-rung **Ladder of Causation** and can never, by
itself and regardless of data volume, answer a question on rungs two or three. Causal claims require
a causal model — a DAG — that is separate from and prior to any data. Stage 0 mirrors this exactly:
judge which rung a question belongs to, and whether the graph plus the observable set make the
target quantity identifiable — never estimate the number.

**The graph is supplied by the user.** This file can never establish that a graph is *true*, only
what is identifiable under it. Therefore assumption provenance is printed with every verdict, not
optionally.

## 2. Frameworks & Structure

### 2.1 The Ladder of Causation (three rungs)
- **Rung 1 — Association / seeing**: "What if I see…?" — conditional probability P(Y|X). What
  standard statistics and machine learning do: detect regularities, predict Y from X. It cannot
  distinguish X causing Y from Y causing X from a common cause of both.
- **Rung 2 — Intervention / doing**: "What if I do…?" — P(Y|do(X)), the probability of Y after
  actively setting X, as opposed to passively observing X at that value. Requires a causal model
  beyond the joint distribution.
- **Rung 3 — Counterfactuals / imagining**: "What if I had done…? / Why?" — requires imagining a
  world contradicting the observed one; needs a structural model, not merely an interventional one.
  "Necessary cause," "sufficient cause," and mediation's natural effects live here.
- **Rule**: "No machine can derive explanations from raw data. It needs a push." A question phrased
  "what if we do X" or "what caused Y" can never be fully answered by association-only evidence,
  however large the dataset. **This is the sentence that makes Stage 0 necessary rather than
  optional**: the push has to come from somewhere, so it should come from an explicit, auditable
  model rather than an unexamined one.

### 2.2 The do-operator and Confounding
- **do(X=x)**: an operator denoting an intervention that sets X to x by external action, erasing all
  arrows pointing *into* X in the graph — as opposed to conditioning on X=x, which leaves those
  arrows and the information they carry intact.
- **Confounding, exact definition**: confounding is present exactly when P(Y|X) ≠ P(Y|do(X)) — when
  passively observing X at a value gives a different answer than actively setting X to it. This is a
  **graph-relative**, not a data-relative, concept, which is why no amount of data settles it.

### 2.3 Chain / Fork / Collider — the three elementary structures
- **(a) Chain** A → B → C: B is a **mediator**. Conditioning on B **blocks** the flow of association
  between A and C.
- **(b) Fork** A ← B → C: B is a **confounder** (common cause). Conditioning on B **blocks** the flow
  and removes the spurious link.
- **(c) Collider** A → B ← C: B is a **collider** (common effect). A and C start out
  **independent**. Conditioning on B **opens** the pipe between A and C, manufacturing a spurious
  association where none existed causally — the "explain-away" effect. This is the *opposite*
  behaviour from (a) and (b), and it is the single most common practical error.
- **(d) Descendants**: conditioning on a descendant partially conditions on the variable itself. A
  descendant of a mediator partially blocks the pipe; a descendant of a collider partially opens it.
- **Reichenbach's common-cause principle** ("no correlation without causation") is refuted by the
  collider structure: colliders produce correlation between variables with no causal connection.

### 2.4 Confounder vs. Mediator vs. Collider — the judgment procedure
1. Draw or elicit the DAG among the variable in question, the treatment, and the outcome.
2. If the variable has two arrowheads pointing **into** it from the other two nodes on a path
   (X→V←Y shape relative to that path), it is a **collider on that path** — do not condition on it
   or on a descendant of it, unless deliberately opening that path for a front-door-style strategy.
3. If the variable lies **on the causal path** from treatment to outcome (X→V→Y), it is a
   **mediator** — conditioning on it blocks part of the very effect being measured (relevant to
   CDE/NDE/NIE in `§2.10`, not to deconfounding).
4. If the variable is a common ancestor of both treatment and outcome, off the direct causal path
   (X←V→Y), it is a **confounder** — generally to be adjusted for, subject to `§2.5`.
5. **M-bias trap**: a collider sitting on the *only* back-door path may already be blocking that path
   by default; conditioning on it — as the naive heuristic "control for anything correlated with both
   X and Y" instructs — *creates* the confounding bias it was meant to remove. Pearl's real case:
   controlling for seat-belt usage, a collider between smoking-related attitudes and
   health-consciousness, manufactures a spurious smoking–lung-disease link.
6. **Never use temporal precedence alone to classify a variable.** "It happened first" does not
   distinguish a confounder from an M-bias collider. Consult the diagram, not the clock.

### 2.5 Back-Door Criterion and Adjustment
- **Back-door path**: any path connecting X to Y that starts with an arrow pointing *into* X.
- **Back-door criterion**: a variable set Z deconfounds X and Y if (i) Z blocks every back-door path
  between X and Y, and (ii) no member of Z is a descendant of X along a causal path from X to Y.
- **Back-door adjustment formula**: P(Y|do(X)) = Σ_z P(Y|X, Z=z) P(Z=z) — a weighted average of
  stratum-specific associational effects, valid **only if** Z satisfies the criterion.
- Ordinary regression coefficients are **not automatically causal**. A coefficient equals a causal
  effect only when the conditioning set satisfies the back-door criterion relative to a correct
  diagram — and "correct diagram" is an assumption the user supplies, never a result this file
  produces.

### 2.6 Front-Door Criterion (deconfounding without observing the confounder)
- Applies when X→Y is confounded by an **unobserved** common cause U, the effect of X on Y is fully
  mediated by an **observed** variable M, M is shielded from U (no arrow U→M), and X has no direct
  effect on Y except through M.
- **Front-door formula**: P(Y|do(X)) = Σ_z P(Z=z|X) Σ_x' P(Y|X=x', Z=z) P(X=x') — deconfounds an
  effect **without ever observing or even naming the confounder**.
- Canonical case: smoking (X) → tar deposits (Z, mediator) → lung cancer (Y), confounded by an
  unobserved smoking-genotype U affecting both smoking propensity and cancer risk directly but not
  through tar. Empirically validated against an RCT benchmark in Glynn & Kashin's JTPA analysis —
  front-door adjustment matched the experimental answer while naive back-door adjustment was badly
  wrong.

### 2.7 do-calculus (three rules) and Identifiability
*Transcribed from this book's informal presentation — see the provenance notice above.*

- **Rule 1 (insertion/deletion of observations)**: P(Y|do(X), Z, W) = P(Y|do(X), Z) if Z blocks every
  path from W to Y in the graph with arrows into X removed.
- **Rule 2 (action/observation exchange)**: P(Y|do(X), Z) = P(Y|X, Z) if Z satisfies the back-door
  criterion relative to (X, Y) — this is what licenses swapping an interventional query for an
  ordinary conditional one.
- **Rule 3 (insertion/deletion of actions)**: P(Y|do(X)) = P(Y) if there is no causal path from X to
  Y in the graph with incoming arrows to X removed.
- **Completeness theorem** (Huang & Valtorta; Shpitser, 2006, independently): if repeated
  application of Rules 1–3 cannot eliminate every do(·) term from a query, then **the query is not
  identifiable from observational data under that graph** — no cleverness and no additional data
  fixes it. The remedies are: run a randomized trial; use an additional identification strategy
  (surrogate variables, or an instrumental variable via Bareinboim's 2012 algorithm); or add new
  measurements that change the graph.
- **This is the formal home of `NotIdentifiable`.** Identifiability is a yes/no property of
  (graph, observable set). When it fails, the correct output names **what would restore it** — an
  instrument, a front-door mediator, an added measurement, an RCT — and still delivers the graph.
  `NotIdentifiable` refuses the claim "this quantity is computable from that graph"; it does not
  refuse to give the user a structure to look at.

### 2.8 Simpson's Paradox (exact structure and resolution)
- **BBG drug example, Pearl's numbers**: Women — 5% heart-attack rate without the drug, 7.5% with
  (drug looks harmful). Men — 30% without, 40% with (drug looks harmful). Aggregated across both —
  22% without, 18% with (drug looks *beneficial*). The sign flips on aggregation.
- **Resolution requires the causal diagram, not the data**: if Gender is a **confounder** (Gender →
  Drug and Gender → HeartAttack), the correct causal answer requires stratifying by gender — the
  aggregate is wrong and the strata are right, and the drug is genuinely harmful in both.
- **Contrast case**: if the third variable is instead a **mediator** on the causal path (Drug →
  BloodPressure → HeartAttack), aggregating is correct and stratifying on the mediator would wrongly
  block part of the causal effect.
- **Rule**: "consult the causal structure of the story, not the temporal information." Identical
  numbers require opposite statistical treatments depending on whether the third variable is
  upstream (confounder) or midstream (mediator), and temporal order does not settle which. Real
  documented instances: the 1996 kidney-stone treatment study; the 1995 thyroid-cancer/smoking
  survival study, confounded by age.

### 2.9 Collider Bias / Berkson's Paradox
- Conditioning on a common effect of two otherwise-independent (or even negatively associated)
  causes creates a **spurious association** between those causes inside the conditioned
  subpopulation.
- **Coin-flip illustration**: flip two independent coins repeatedly and discard every tail-tail
  outcome; among the retained outcomes the coins now appear correlated, though nothing links them.
- **Berkson's paradox (1946), real data**: hospitalized patients show spurious correlations between
  unrelated diseases because hospitalization — a collider, caused by either disease — is being
  implicitly conditioned on. Sackett (1979): bone disease affects roughly 7.5% of the general
  population but roughly 25% of hospitalized respiratory patients, an artifact of conditioning on
  hospitalization rather than a causal link.
- **Stage 0 note**: the conditioning is usually **implicit** — a filtered sample, a
  survivorship-selected cohort, a self-selected user group. Any population defined by a behaviour
  that the outcome also causes is a candidate `ConditioningOnCollider`.

### 2.10 Mediation — Direct, Indirect, and Total Effects
- **Controlled Direct Effect, CDE(m)** = P(Y=1|do(X=1), do(M=m)) − P(Y=1|do(X=0), do(M=m)) —
  computable from do-calculus alone (rung 2); holds the mediator fixed at a chosen value by
  intervention.
- **Natural Direct Effect, NDE** — the effect of X on Y with the mediator held at whatever value it
  would **naturally** have taken under the *other* treatment condition. Requires counterfactual
  notation (rung 3); not reducible to a do-expression; needs the Mediation Formula to become
  estimable from observational data.
- **Natural Indirect Effect, NIE** — likewise rung 3; estimable from data only under a
  "no confounding between mediator and outcome" assumption.
- **Additivity holds only in linear models**: Total = Direct + Indirect is a linear-model-only
  identity (sums of path-coefficient products). Under nonlinearity or interaction it **fails** —
  Pearl's enzyme/catalyst example has a positive total effect while *both* direct and indirect
  effects individually equal zero.
- **General (nonlinear-safe) identity**: Total Effect(0→1) = NDE(0→1) − NIE(1→0) — a subtraction of
  oppositely-indexed terms, not a sum. This form survives nonlinear and threshold settings.
- **Baron-Kenny regression (1986)** is the dominant applied approach (70,000+ citations) but is
  **not causally grounded** and breaks under nonlinearity. A job-salary-threshold example gives
  CDE(0) ≠ CDE(2): the direct effect's magnitude depends on the value at which the mediator is held,
  which a single-coefficient framing cannot represent.
- **This is the exact technical home of "mediator."** No other source in this library supplies a
  rigorous mediator / confounder / collider three-way test; when a case hinges on that
  classification, Pearl is the only citable authority here.

## 3. Decision Rules & Judgment

- Rung check first: does the question ask what is *associated with*, what happens if we *do*, or what
  *would have happened if*? Route to rung 1/2/3 before anything else. A rung-2-or-3 question can
  never be fully answered by rung-1 evidence — if the user asserts a causal or interventional claim
  on association-only evidence, that assertion is refused as
  `CausalClaimFromObservationalOnly`.
- Before adjusting for *any* variable, classify it as confounder / mediator / collider by DAG shape —
  never by temporal order, never by "it correlates with both."
- If a collider or its descendant is being conditioned on — including implicitly, via a selected or
  filtered sample: self-selection, survivorship, hospitalization — flag `ConditioningOnCollider`.
- If the causal path runs through an unobserved variable with no valid adjustment set and no mediator
  satisfying the front-door shielding condition, flag `UnobservedConfounder` or `NotIdentifiable`,
  and name exactly what added structure would fix it: an instrument, a front-door mediator, a natural
  experiment, a randomized trial.
- **Refuse the claim, not the request.** Every verdict in this file rejects an assertion about what
  can be computed. In every case the elicited graph, its commitments and its prohibitions are still
  delivered — that is the deliverable, and it is what tells the user where to look next.
- Print assumption provenance with every verdict: which arrows the user asserted, which were proposed
  here, and which are load-bearing for the identifiability conclusion.
- Never output a numeric effect size, probability or point estimate — this file supports
  identifiability judgment and structural classification only, per the NOTICE.

## 4. Key Takeaways

1. The rung of the Ladder of Causation is the first fork: association vs. intervention vs.
   counterfactual, decided before anything else.
2. Confounder / mediator / collider is a DAG-shape question, never a temporal-order or
   correlation-strength heuristic. Get it wrong and the direction of the bias flips.
3. Colliders reverse the usual rule: conditioning on them *creates* spurious association instead of
   removing it — M-bias, Berkson, and Simpson in its confounder form.
4. Identifiability is decidable via the three do-calculus rules; failure names a specific missing
   structural ingredient, never "need more data."
5. The graph is an input, not a finding. This source can say what follows from a graph and never that
   the graph is true — hence mandatory assumption provenance.
6. This source builds judgment, not measurement. Never produce an effect-size number from it.
