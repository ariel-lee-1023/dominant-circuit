# Thinking in Systems: A Primer — Donella H. Meadows

**Format**: epub | **Pages**: ~240 | **Depth**: reference | **Anchors**: `§N`, `§N.M`

> **Role in Stage 0 — the noun supplier.** This book answers one question: *what is there to look
> at?* Without the vocabulary of stocks, flows, loops and delays, a person cannot see accumulation,
> and cannot see the oscillation that delays produce. Meadows also supplies the constitutional
> reason Stage 0 exists at all: the system boundary is **chosen**, not discovered (`§2.4`) — so
> some prior commitment is unavoidable, and the only question is whether it is made deliberately.
> This book never picks a policy, and neither does Stage 0.

## 1. Mental Model (read first)

A system is not a pile of parts; it is a set of **stocks** connected by **flows**, held together by
**feedback loops**, that produces its own behaviour over time. Meadows's core discipline: before
naming a policy or an intervention, draw the boundary, name what accumulates, name what moves, and
trace the loops — because a system's structure, not the intentions of the people inside it,
determines its behaviour.

## 2. Frameworks & Structure

### 2.1 Stocks and Flows (the atomic vocabulary)
- **Stock**: the memory of a system — an accumulation measurable at one instant; it exists whether
  or not any flow is currently moving. Water in a bathtub, money in an account, population,
  goodwill, pending tickets.
- **Flow**: a rate — inflow (fills the stock) or outflow (drains it) — measured per unit time.
- **Dimensional rule (the only free self-check)**: a stock's unit must equal a flow's unit × time.
  If a proposed "stock" cannot be expressed that way it has been misnamed — it is really a flow, a
  rate, or not a system-dynamics quantity at all. Stage 0 runs this mechanically before accepting
  any construct name (capability 5.2); failure is `DimensionalMismatch`.
- **How stocks behave**: a stock changes only when inflow ≠ outflow; it acts as a buffer/delay
  between flows even when the flows are erratic; you can know a stock's value without knowing
  either flow rate. Stocks give systems inertia and memory — this is *why* a system does not
  respond instantly to a changed input.

### 2.2 Feedback Loops
- **Balancing (negative) loop**: opposes whatever direction of change is imposed on the stock;
  seeks a goal or equilibrium and resists disturbance. Signature: self-correcting, stabilizing,
  goal-seeking.
- **Reinforcing (positive) loop**: amplifies a direction of change — more begets more, less begets
  less. Signature: self-multiplying, destabilizing if unchecked, exponential growth or collapse.
- **Loop polarity is a property of loop structure, not of whether the outcome feels good.** A
  reinforcing loop is not inherently bad (compounding savings); a balancing loop is not inherently
  good (a thermostat stuck at the wrong setpoint).
- **Loop dominance**: real systems contain multiple loops of both polarities operating at once;
  behaviour at any moment is set by whichever loop(s) currently dominate. Dominance can **shift** as
  stock levels change the loops' relative strengths — and that shift is itself a primary source of
  surprising nonlinear behaviour. An S-shaped growth curve *is* reinforcing-loop dominance handing
  off to balancing-loop dominance as a constraint is approached.
- **Stage 0 consequence**: when opposite-polarity loops are present and stated information cannot
  settle which dominates, the verdict is `LoopDominanceUndetermined` — and it must arrive with the
  measurement that would settle it (typically: the two loops' gains at current stock levels).
  Never guess a lever direction (`§2.5`).

### 2.3 Delays
- **Delay**: the lag between a change in a flow (or a decision) and its full effect on a stock, or
  on the information that feeds back to the decision-maker. Delays are structural properties, not
  modelling inconveniences.
- Delays determine how fast a system can react, how accurately it hits a target, and how stale the
  information circulating in it is. **"Overshoots, oscillations, and collapses are always caused by
  delays."**
- A decision-maker responding to delayed information will systematically over- or under-correct —
  this alone generates oscillation even when every loop's polarity is "correct." So for any
  control/response case, ask *where is the delay, and is it in the information channel or in the
  physical flow?* before any claim about which loop is failing.
- Delay length is usually a **weak** lever in practice (`§2.5`) because most delays are physically
  fixed — a child's maturation, a forest's growth, a factory's construction. The available lever is
  usually slowing the *rate* that must pass through the delay, not shortening the delay.

### 2.4 System Boundary — why prior commitment is unavoidable
- The boundary is a **modelling choice**, not a fact discovered in the world: "there are no separate
  systems… The world is a continuum. Where to draw a boundary depends on the purpose of the
  discussion." A system has no single correct boundary; it has a boundary appropriate to the
  question being asked.
- **This is the load-bearing justification for Stage 0.** Since no boundary is given by the world,
  observation cannot begin until one is chosen. A person with no declared boundary is not neutral —
  they are using an undeclared one.
- **Stage 0 consequence, and it is the opposite of a refusal**: if the user's framing never commits
  to what is inside vs. exogenous, do **not** stop at "boundary undeclared." Emit `BoundaryFork` —
  2–3 candidate boundaries, each stated together with what it makes exogenous and therefore which
  questions it forbids. Different boundaries can produce contradictory correct answers to the same
  question, which is exactly why the choice must be surfaced to the user rather than made silently
  on their behalf, and exactly why declining to offer candidates leaves the user worse off than
  before they asked.

### 2.5 Leverage Points (Meadows's 12-point hierarchy, low → high leverage)
Meadows's own list, ascending in power (paraphrased; the specific numeric parameters vary by system):

1. **Constants, parameters, numbers** (subsidies, taxes) — lowest leverage; the place everyone
   fights over and the place that changes least.
2. **Buffer sizes** — the size of stabilizing stocks relative to their flows; usually hard to change
   (a dam's storage capacity is cast in concrete).
3. **Physical structure** (the stocks and flows themselves, e.g. a road network) — leverage exists
   mainly at design time, not after construction.
4. **Delays** — length of time relative to rates of change; often not easily changeable ("things
   take as long as they take"), so leverage more often lies in slowing the rate that must pass
   through a fixed delay.
5. **Balancing loop strength** — the power of a correcting loop relative to the disruption it must
   correct (market price signals).
6. **Reinforcing loop strength** — the gain around a self-multiplying loop. **Reducing the gain of a
   reinforcing loop is usually a more powerful lever than strengthening a balancing loop**, and far
   preferable to letting the reinforcing loop run unchecked (Meadows's World-model growth example).
7. **Information flows** — who does and does not have access to what; adding a missing feedback link
   can change behaviour cheaply.
8. **Rules** — incentives, punishments, constraints; the rules of the game (a constitution, an
   incentive scheme).
9. **Self-organization** — the power to add, change, or evolve system structure itself.
10. **Goals** — the purpose the system is oriented toward; changing the goal redirects every loop
    beneath it.
11. **Paradigms** — the shared mindset out of which goals, structure and rules arise.
12. **Power to transcend paradigms** — highest leverage: holding paradigms as provisional.

- **Governing warning (load-bearing).** Meadows states that leverage points are strongly
  **counterintuitive**: people who intuitively "know" where the leverage is very often push in the
  *wrong direction* — Forrester's observation that managers can name the problem and the structure
  accurately and still get the sign of the lever wrong. **Therefore Stage 0 never proposes a
  leverage direction or a policy ranking.** That inference is downstream, structurally unreliable
  without a running model, and out of scope for a body that only names structure.
- **Computability boundary.** Ranks 1–4 (parameters, buffers, physical structure, delays) admit
  sensitivity ranking *within a given structure*. Ranks 8–12 (rules, self-organization, goals,
  paradigms) are **not computable** and must be reported as hard constraints — "this lies outside
  what can be calculated" — rather than dressed up as a result.

### 2.6 Common Systems Traps / Archetypes (diagnostic patterns, not policy advice)
- **Policy resistance ("fixes that backfire")**: multiple actors pull the same stock toward their
  own different goals via separate balancing loops; each fix is offset by another actor's
  counter-correction, so the stock barely moves despite rising effort from all sides. Fingerprint:
  "we tried harder and it did not help — it got more effortful to hold the same place."
- **Tragedy of the commons**: a shared replenishable stock is drawn down by independent agents whose
  individual balancing loops do not see the depletion signal until much later (delay-obscured); the
  reinforcing structure of individual gain outruns the shared balancing signal.
- **Escalation**: two reinforcing loops cross-coupled — each side's stock rises in response to the
  other's — producing runaway competitive buildup.
- **Success to the successful**: a reinforcing loop in which the current leader's success increases
  their share of a limited resource, which increases future success.
- **Shifting the burden / addiction**: a quick balancing fix on a *symptom* substitutes for a slower
  structural fix on the underlying stock, and reliance on the quick fix atrophies the capacity for
  the structural fix. Structural fingerprint: a parameter-level lever (rank 1) is applied to a
  system whose actual constraint is loop dominance or a delay, further up the hierarchy — so effort
  rises while the stock does not move.
- **Drift to low performance**: the perceived standard is set by recent (declining) performance
  rather than an absolute goal, so the goal itself erodes in a reinforcing loop.

## 3. Decision Rules & Judgment

- Before naming any variable a stock, run the dimensional rule: can its unit be produced by
  integrating some flow's unit over time? If not, it is not a stock.
- Before diagnosing "the intervention is not working," ask whether a reinforcing loop is being fed
  *by* the intervention — a common structure is that added capacity increases visible pending work,
  which increases new-work arrival, offsetting the capacity added. Do not default to "the fix was
  too small"; ask whether the fix targeted the dominant loop.
- Never accept a described system without an explicit boundary — **and never stop there either.**
  If the boundary is not stated and cannot be read off what the user already specified (not guessed
  from their intent), emit `BoundaryFork` with candidate boundaries and their prohibitions.
- If a described mechanism has no accumulating quantity anywhere — no memory, no stock — the case is
  not a dynamics problem. Route it as **static**: a one-shot decision, not a system to be diagnosed
  for loops and delays.
- Never rank candidate leverage points or recommend which lever to pull. Meadows's own warning about
  wrong-signed intuition applies with full force to any distillation of his book; leverage selection
  is downstream of Stage 0.
- When a complaint has the shape "we did X, an obvious lever, and it did not help or made things
  worse," treat this as presumptive evidence of an unnamed reinforcing loop or an unaddressed delay,
  and ask for the missing stocks (backlog stock, skill/experience stock, trust stock) before any
  further judgment.
- Mark every construct as user-stated or Stage-0-added. An added stock is a proposal; an unmarked
  added stock is the analyst's opinion wearing the user's name.

## 4. Key Takeaways

1. Structure — stocks, flows, loop polarity, delays, boundary — determines behaviour; never
   substitute a policy opinion for naming these constructs.
2. The stock/flow dimensional check (unit = rate × time) is the only mechanical, free self-audit at
   this layer. Always run it.
3. "We intervened and it got worse" is the fingerprint of reinforcing-loop dominance or
   delay-driven overcorrection, not evidence the intervention was merely undersized.
4. The boundary is chosen for a purpose, not discovered — which is why an undeclared boundary is a
   fork to be surfaced with candidates, not a dead end to be reported.
5. Leverage-point intuition is famously wrong-signed. Stage 0 stops at naming structure and never
   recommends where to push; ranks 8–12 are not computable at all.
