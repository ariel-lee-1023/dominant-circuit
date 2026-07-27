# Cluster 01: Optimal Stopping

**Source**: *Algorithms to Live By* (Brian Christian & Tom Griffiths), Chapter 1, "Optimal Stopping: When to Stop Looking"

## Scope

Zero-order mechanisms for deciding when to stop a sequential search and commit to an option, under varying information conditions. Covers the classical secretary problem, the discrete-\(n\) and asymptotic solutions, the Look-Then-Leap Rule, the Threshold Rule under full information, recall/rejection variants, cost-of-search formulations (house-selling, parking), duration-maximizing and unknown-horizon adaptations, and the conditions under which no optimal stopping rule exists at all.

---

## 1. Classical Secretary Problem: Assumptions

The zero-order model requires all of the following to hold. Any relaxation moves the problem into a named variant (Section 5+).

1. There is a known, fixed number of options \(n\) (applicants), presented strictly one at a time in random order (all \(n!\) orderings equally likely).
2. For each option observed, the decision-maker can determine only its **relative rank** against options seen so far (ordinal information), not its **absolute value** (cardinal information). This is the "no-information game."
3. At each step, the decision-maker must either **accept** (irrevocably ending the search) or **reject** (irrevocably discarding that option forever; no recall).
4. An accepted offer is always available and always accepted by the option (no rejection risk).
5. The objective is to maximize the probability of selecting the single best option in the entire pool of \(n\), not to maximize expected rank, expected value, or any other payoff structure.

**Anti-pattern**: applying the 37% figure to a search where any of these assumptions is violated (unknown \(n\), cardinal/full information available, recall possible, rejection possible, or a payoff other than "best-or-nothing") without first checking which variant applies (Section 8).

---

## 2. Why Early Best-Yet Candidates Are Uninformative

- A candidate is only worth considering if it is "best-yet" (better than all previously seen options), since accepting a non-best-yet candidate can never yield the overall best.
- The probability that the \(k\)-th candidate observed is best-yet, absent any decision policy, is \(1/k\): candidate 1 is trivially best-yet (probability 1), candidate 2 has probability \(1/2\), candidate 5 has probability \(1/5\), etc.
- **Invariant**: best-yet candidates become rarer but more informative as the search progresses; accepting the very first best-yet candidate (i.e., candidate 1) is provably suboptimal because it uses zero comparative information.

---

## 3. The Look-Then-Leap Rule

**Definition**: Set a predetermined position \(r\) (out of \(n\)) that divides the search into two phases:
- **Look phase** (positions \(1\) to \(r-1\)): observe every candidate, record the best-yet seen, reject all candidates unconditionally regardless of quality.
- **Leap phase** (positions \(r\) to \(n\)): accept the first candidate encountered that is better than every candidate seen in the look phase. If no such candidate appears, the policy is forced to accept the last candidate (\(n\)-th).

**Pseudocode**:
```
function look_then_leap(candidates: list[n], r: int) -> index:
    best_in_look_phase = -infinity
    for i in 1..r-1:
        best_in_look_phase = max(best_in_look_phase, rank(candidates[i]))
        # reject unconditionally
    for i in r..n:
        if rank(candidates[i]) > best_in_look_phase:
            return i   # leap: accept
    return n           # forced acceptance of final candidate
```

**Inputs**: ordered sequence of \(n\) candidates revealed one at a time; only pairwise/relative comparisons available.
**Output**: index of accepted candidate.
**Invariant**: the only free parameter is \(r\); the rule's entire behavior is determined by where the look/leap boundary is placed.

---

## 4. Discrete-\(n\) Solution and the Threshold's Convergence

Small-\(n\) enumeration establishes the boundary placement inductively:

| \(n\) (applicants) | Optimal look-phase length (leap starts at) | Success probability |
|---|---|---|
| 1 | leap immediately (accept candidate 1) | 100% |
| 2 | leap immediately | 50% |
| 3 | look at 1, leap from candidate 2 | 50% (vs. 33% random) |
| 4 | leap from candidate 2 | converges toward pattern |
| 5 | leap from candidate 3 | N/A |
| large \(n\) | leap starts at \(\approx 0.37n\) | \(\to 37\%\) |

**Reasoning invariant for \(n=3\)**: candidate 1 carries no information (always "best-yet" by definition); candidate 3 carries no agency (must be taken if reached, since 1 and 2 are already rejected); only candidate 2 carries both information (comparable to candidate 1) and agency (can be accepted or rejected). The optimal rule: accept candidate 2 if and only if it beats candidate 1, otherwise fall through to candidate 3. This achieves 50% success versus 33% for random selection.

**General finite-\(n\) computation**: the optimal cutoff \(r\) and its success probability are found by backward induction, evaluating, for each candidate position \(i\), the probability that stopping there (conditional on it being best-yet) exceeds the expected value of continuing to look. As \(n\) grows, both the normalized cutoff \(r/n\) and the success probability converge to the same constant.

**Exact finite-\(n\) success formula**: for a Look-Then-Leap policy with look-phase length \(r-1\) (i.e., leaping begins at position \(r\)), the probability of ending up with the single best candidate is

\[
P_n(r) = \frac{r-1}{n} \sum_{j=r}^{n} \frac{1}{j-1}, \qquad 2 \le r \le n
\]

with the boundary case \(P_n(1) = 1/n\) (leaping immediately is equivalent to picking uniformly at random).

The optimal cutoff \(r^{*}(n)\) is the integer \(r\) that maximizes \(P_n(r)\); it must be found by direct evaluation (finite-\(n\) argmax, Section 4.1).

### 4.1 Finite-\(n\) Argmax Pseudocode

```
function optimal_cutoff(n: int) -> (r_star: int, p_star: float):
    best_r, best_p = 1, 1.0 / n
    for r in 2..n:
        harmonic_tail = sum(1.0 / (j - 1) for j in r..n)
        p = ((r - 1) / n) * harmonic_tail
        if p > best_p:
            best_r, best_p = r, p
    return (best_r, best_p)
```

---

## 5. Asymptotic \(1/e\) Result

For large \(n\), both the optimal look-fraction and the resulting maximum success probability converge to \(1/e \approx 0.368\).

**Look-Then-Leap Rule at scale (the "37% Rule")**: look at (reject) the first \(\approx 37\%\) of candidates unconditionally, recording the best seen; thereafter, accept the first candidate that beats all of them.

---

## 6. Full-Information Variant: The Threshold Rule

**Threshold Rule**: immediately accept a candidate if its score exceeds a threshold computed from how many candidates remain.

Approximate closed-form:

\[
t_k = \frac{1}{1 + 0.804/k + 0.183/k^2}
\]

Success probability under full information: \(\approx 58\%\).

---

## 7. Recall and Rejection Variants

- Rejection (50% accept rate): begin proposing after the first quarter (\(r/n \approx 0.25\)); success \(\approx 25\%\).
- Recall (50% delayed-acceptance): look to \(\approx 61\%\), then leap or fall back; success \(\approx 61\%\).

Do not reuse these constants outside their calibrated assumption sets.

---

## 8. Hard Conditions Where 37% Is Invalid

The 37% figure is specific to the classical assumption set. See the Decision Table for the correct constant under each variant. Diverging-expectation games admit no optimal stopping rule.

---

## 9. Search-Cost Formulations

Cost-aware threshold (house-selling): solve \((1-p)^2/2 = c\) for the fixed threshold \(p^* = 1 - \sqrt{2c}\). The threshold never decreases over time; recall is never optimal.

---

## 10. Spatial / Duration Analog: The Parking Problem

Same mathematical family as Section 9, restated over distance instead of price, with a discrete occupancy parameter.

**Setup**: an unbounded sequence of parking spots at fixed spacing, each independently occupied with probability equal to the **occupancy rate** \(p\). Objective: minimize walking distance to a fixed destination.

**Rule**: Look-Then-Leap over distance; ignore all empty spots farther than a computed cutoff distance from the destination, then take the first empty spot found at or within that distance.

**Cutoff formula** (corrected; see SPEC §12 / D-03):

\[
d^{*} = \left\lfloor \frac{-\log 2}{\log p} \right\rfloor
\]

spots from the destination, where \(p\) is the occupancy rate (probability any given spot is occupied).  
(The probability that \(d\) consecutive spots are all occupied is \(p^d\). Setting \(p^d = 1/2\) and solving yields the expression above.)

**Worked values** (corrected form):

| occupancy \(p\) | \(d^{*}\) |
|---|---|
| 0.50 | 1 |
| 0.85 | 4 |
| 0.90 | 6 |
| 0.95 | 13 |
| 0.99 | 68 |

**Invariant**: higher occupancy rate \(\to\) larger cutoff distance \(\to\) must start "seriously looking" farther from the destination. The relationship is highly nonlinear near \(p=1\): moving occupancy from 90% to 95% (a 5.5% relative increase) roughly doubles the expected search length (exact unfloored ratio \(\approx 2.05\).

**Anti-pattern (policy-level)**: treating high occupancy as evidence of efficient resource utilization; under this model, near-100% occupancy imposes large, hidden search costs not captured by the occupancy metric alone. An occupancy rate around 85–90% is commonly cited as balancing utilization against search cost.

---

## 11. Duration / Unknown-Horizon and "Quit While Ahead" Adaptations

Burglar ceiling: \(\text{ceiling} = mq/(1-q)\).

Unknown-horizon and stochastic-termination variants replace fraction-of-\(n\) cutoffs with cutoffs based on a stopping-probability parameter or an assumed distribution over \(n\).

---

## Compact Worked Algorithm (General-Purpose Optimal Stopping Selector)

See the decision table and classify_and_solve dispatch in the original corpus. Every finite-\(n\), best-or-nothing, ordinal-information variant without recall or rejection converges to \(1/e\) as \(n \to \infty\); this constant is a signature of that specific assumption set, not a universal law.

---

## Decision Table: Which Rule Applies

| Information | Horizon | Recall? | Rejection risk? | Payoff | Rule | Optimal look-phase / threshold | Success rate |
|---|---|---|---|---|---|---|---|
| Ordinal only | Fixed, known \(n\) | No | No | Best-or-nothing | Look-Then-Leap (37% Rule) | \(r \approx n/e \approx 0.37n\) | \(\approx 37\%\) |
| Cardinal (full) | Fixed, known \(n\) | No | No | Best-or-nothing | Threshold Rule | \(t_k = 1/(1+0.804/k+0.183/k^2)\) | \(\approx 58\%\) |
| Ordinal only | Fixed, known \(n\) | Yes (50% recall-accept) | No | Best-or-nothing | Look-Then-Leap + fallback recall | \(r \approx 0.61n\) | \(\approx 61\%\) |
| Ordinal only | Fixed, known \(n\) | No | Yes (50% accept) | Best-or-nothing | Early-and-often proposing | \(r \approx 0.25n\) | \(\approx 25\%\) |
| Ordinal only | Unknown \(n\), uniform on \([1,n_{max}]\) | No | No | Best-or-nothing | Look-Then-Leap | \(r \approx n_{max}/e^2 \approx 0.135\,n_{max}\) | \(2/e^2 \approx 27\%\) |
| Ordinal only | Open-ended, stops w.p. \(p\) per step | No | No | Best-or-nothing | Look-Then-Leap | \(r \approx 0.18/p\) | \(\approx 23.6\%\) |
| Cardinal (full) | Unbounded stream, per-offer cost \(c\) | Never optimal | N/A | Net value minus search cost | Cost-Aware Threshold | fixed \(p^{*}\) solving \((1-p)^2/2 = c\) | scenario-dependent |
| Ordinal/positional | Unbounded spatial sequence, occupancy \(p\) | No | No | Minimize distance | Parking Threshold | \(d^{*} = \lfloor -\log 2/\log p\rfloor\) | scenario-dependent |
| N/A | Repeated trials, ruin on failure | N/A | N/A | Accumulate then stop | Burglar Rule | ceiling \(= mq/(1-q)\) | scenario-dependent |
| N/A | Any | N/A | N/A | Reward diverges at best stopping point | **No rule exists** | undefined | undefined |

---

## Key Invariants Across All Variants

1. Every finite-\(n\), best-or-nothing, ordinal-information variant without recall or rejection converges to the same look/success constant \(1/e \approx 0.37\) as \(n \to \infty\).
2. Adding cardinal information strictly increases achievable success probability and collapses Look-Then-Leap into a Threshold Rule.
3. Rejection risk shortens the look phase; recall with imperfect acceptance lengthens it.
4. Fixed per-step cost makes the threshold static and forecloses recall.
5. A stopping rule requires finite expected payoff at the best stopping point.
