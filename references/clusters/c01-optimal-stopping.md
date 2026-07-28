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

with the boundary case \(P_n(1) = 1/n\) (leaping immediately is equivalent to picking uniformly at random). This follows from conditioning on the position \(i\) of the overall best candidate: the policy succeeds only if the best candidate lands at some position \(i \ge r\) **and** the best candidate among positions \(1..i-1\) is confined to the look phase (positions \(1..r-1\)), which occurs with probability \((r-1)/(i-1)\). Summing \(\frac{1}{n}\cdot\frac{r-1}{i-1}\) over \(i=r,\dots,n\) yields the formula above (reindexing the summation variable as \(j=i\) gives the stated form).

The optimal cutoff \(r^{*}(n)\) is the integer \(r\) that maximizes \(P_n(r)\); it must be found by direct evaluation (finite-\(n\) argmax, Section 4.1) since no simple closed form exists for finite \(n\).

### 4.1 Finite-\(n\) Argmax Pseudocode

```
function optimal_cutoff(n: int) -> (r_star: int, p_star: float):
    best_r, best_p = 1, 1.0 / n
    for r in 2..n:
        harmonic_tail = sum(1.0 / (j - 1) for j in r..n)   # sum_{j=r}^{n} 1/(j-1)
        p = ((r - 1) / n) * harmonic_tail
        if p > best_p:
            best_r, best_p = r, p
    return (best_r, best_p)
```

**Inputs**: pool size \(n\). **Output**: optimal cutoff position \(r^{*}\) and its exact success probability \(P_n(r^{*})\). **Invariant**: this brute-force evaluation is exact for any finite \(n\) and is the reference against which the asymptotic \(1/e\) approximation (Section 5) should be checked for small or moderate \(n\).

---

## 5. Asymptotic \(1/e\) Result

**Harmonic-sum / logarithm approximation**: for large \(n\), the tail sum in \(P_n(r)\) approximates a natural logarithm,

\[
\sum_{j=r}^{n} \frac{1}{j-1} \approx \ln\!\left(\frac{n}{r-1}\right) \approx \ln\!\left(\frac{n}{r}\right)
\]

so, writing \(x = r/n\) (the fraction of the pool spent looking),

\[
P_n(r) \approx x \ln\!\left(\frac{1}{x}\right) = -x \ln x
\]

**Calculus derivation of \(x = 1/e\)**: differentiate \(f(x) = -x\ln x\) with respect to \(x\) and set the derivative to zero:

\[
f'(x) = -\ln x - 1 = 0 \quad \Longrightarrow \quad \ln x = -1 \quad \Longrightarrow \quad x = \frac{1}{e}
\]

The second derivative \(f''(x) = -1/x < 0\) confirms this is a maximum, not a minimum. Substituting back:

\[
f(1/e) = -\frac{1}{e}\ln\frac{1}{e} = \frac{1}{e} \approx 0.368
\]

So both the optimal look-fraction and the resulting maximum success probability converge to the same constant \(1/e\). As \(n \to \infty\):

\[
\frac{r^{*}}{n} \to \frac{1}{e} \approx 0.368
\]

\[
P_n(r^{*}) \to \frac{1}{e} \approx 0.368
\]

**Look-Then-Leap Rule at scale (the "37% Rule")**: look at (reject) the first \(\approx 37\%\) of candidates unconditionally, recording the best seen; thereafter, accept the first candidate that beats all of them.

**Invariant (scale-invariance)**: this \(37\%\) success probability does not degrade as \(n\) grows; it holds equally for \(n=100\) and \(n=1{,}000{,}000\), unlike random selection whose success probability is \(1/n\) and vanishes as \(n\) grows. The value of using the optimal algorithm therefore increases with pool size, even though the algorithm still fails roughly \(63\%\) of the time.

**Anti-pattern**: assuming a bigger applicant pool makes finding the single best option harder in relative terms under the optimal policy. It does not: the failure rate is constant, not increasing, when the algorithm is followed.

---

## 6. Full-Information Variant: The Threshold Rule

Relaxes assumption 2 above: candidates can be scored on an objective, known scale (e.g., a percentile), so the decision-maker has "full information," not merely relative ranks.

**Threshold Rule**: immediately accept a candidate if its score exceeds a threshold computed from how many candidates remain; no look phase is required to calibrate; the threshold is set purely from the count of remaining opportunities.

**Backward-induction structure** (informal): starting from the last candidate (must accept, threshold = 0), threshold percentiles rise as more candidates remain:
- Last candidate: accept unconditionally.
- Second-to-last: accept if above the 50th percentile, else fall through.
- Third-to-last: accept if above the 69th percentile.
- Fourth-to-last: accept if above the 78th percentile.
- Threshold increases (becomes more selective) monotonically as more candidates remain; decreases (becomes more permissive) monotonically as options dwindle.

**Approximate closed-form** for the threshold on candidate \(n-k\) (i.e., with \(k\) candidates remaining after this one, so \(k=0\) is the last candidate, \(k=1\) is second-to-last, etc.):

\[
t_k = \frac{1}{1 + 0.804/k + 0.183/k^2}
\]

\(t_k\) is itself the **percentile-score cutoff**: accept candidate \(n-k\) if and only if its own percentile score is at or above \(t_k\), i.e. \(\text{score} \ge t_k\). Equivalently, accept if the probability that a random future candidate would outscore this one, \(1 - \text{score}\), is less than or equal to \(1 - t_k\). This matches the book's own worked values: \(t_1 \approx 0.50\) (accept the second-to-last candidate only above the 50th percentile), \(t_2 \approx 0.69\) (third-to-last above the 69th percentile), \(t_3 \approx 0.78\) (fourth-to-last above the 78th percentile).

As \(k\) grows (more candidates remain), the denominator \(1 + 0.804/k + 0.183/k^2\) shrinks toward 1, so \(t_k\) **rises** toward 1: the policy becomes more selective the earlier it is in the search. As the search proceeds and \(k\) falls toward 0, \(t_k\) **falls** toward 0: the policy becomes steadily more permissive, exactly mirroring the backward-induction table above.

**Pseudocode**:
```
function threshold_rule(candidates: list[n], percentile_score: fn) -> index:
    for i in 1..n:
        k = n - i                     # candidates remaining after this one
        t_k = 1 / (1 + 0.804/k + 0.183/k**2)  if k > 0 else 0
        if percentile_score(candidates[i]) >= t_k:
            return i    # accept: score clears the current threshold
    return n            # forced acceptance
```

**Success probability under full information**: \(\approx 58\%\), versus \(37\%\) under no information; full information strictly dominates.

**Invariant**: full information eliminates the need for an unconditional look phase; the entire policy is expressible as a threshold, not a two-phase rule. "Look-Then-Leap" degenerates into pure "Threshold" behavior once cardinal information exists.

**Anti-pattern**: running an uncalibrated look phase (rejecting candidates outright regardless of score) when full information is actually available; this discards usable information and yields the strictly worse \(37\%\) success rate instead of \(58\%\).

---

## 7. Recall and Rejection Variants (Look-Then-Leap with a Twist)

Relaxes assumptions 3 and 4 (no recall; guaranteed acceptance).

**Rejection allowed** (offers can be turned down by the candidate):
- If a proposal has a fixed 50% chance of rejection, begin proposing after the first quarter of the pool (\(r/n \approx 0.25\)), and continue proposing to every best-yet candidate encountered until one accepts.
- Resulting overall success probability: \(\approx 25\%\).
- **General principle**: as rejection risk rises, the optimal look phase shortens and proposals must resume "early and often."

**Recall allowed** (a previously passed-over option can be revisited, though acceptance is no longer guaranteed):
- If a belated (recalled) proposal is accepted only half the time while an immediate proposal is always accepted, the optimal look phase lengthens to \(\approx 61\%\) of the pool. Only leap during the remaining \(39\%\) for a best-yet candidate; if none appears, fall back and recall the best candidate from the look phase.
- Resulting success probability: \(\approx 61\%\) (again numerically equal to the look-phase proportion; the same look/success symmetry seen in the classical 37% case).
- **Fallback plan structure**: recall variants require the policy to retain a pointer to the best candidate seen so far even after the look phase ends, so it can be invoked if the leap phase produces no acceptance.

**Pseudocode (recall variant)**:
```
function look_then_leap_with_recall(candidates: list[n], r: int, recall_accept_prob: float) -> index_or_none:
    best_look = argmax(rank(candidates[1..r-1]))
    for i in r..n:
        if rank(candidates[i]) > rank(candidates[best_look]):
            return i                     # leap: immediate proposal, always accepted
    # fallback: recall the best-yet candidate from the look phase
    if bernoulli_trial(recall_accept_prob):
        return best_look                 # recalled proposal accepted
    else:
        return none                      # recalled proposal refused; search ends without a hire
```

**Calibration caveat**: the cutoff \(r \approx 0.61n\) and the resulting \(\approx 61\%\) success figure are calibrated specifically for the case where immediate proposals are always accepted and belated (recalled) proposals are accepted with probability \(0.5\). A different `recall_accept_prob` requires recomputing \(r\) from the underlying optimization; do not reuse \(0.61\) for other acceptance probabilities. An earlier, simplified version of this pseudocode returned `best_look` unconditionally on fallback, silently assuming recall always succeeds; only the version above, with the explicit `bernoulli_trial` step, correctly models the possibility of refusal.

**Invariant**: rejection risk (candidate may decline) **shortens** the required look phase relative to the classical 37% baseline (\(r/n\) drops from \(\approx 0.37\) to \(\approx 0.25\)), because delaying the first proposal too long wastes opportunities that might have been accepted. Recall (decision-maker may revisit a passed-over option) **lengthens** the required look phase (\(r/n\) rises from \(\approx 0.37\) to \(\approx 0.61\)), because more looking is safe when a fallback to the best-yet candidate remains available. The two variants also move achievable success probability in opposite directions relative to the 37% baseline: the 50%-rejection case (Section 8 table) lowers overall success to \(\approx 25\%\), while the 50%-delayed-acceptance recall case raises it to \(\approx 61\%\). Do not conflate the two: shortened look phase pairs with reduced success (rejection), lengthened look phase pairs with increased success (recall).

---

## 8. Hard Conditions Where 37% Is Invalid

The 37% figure is specific to the classical no-information, best-or-nothing, no-recall, no-rejection, fixed-\(n\) formulation. It does not transfer to the following situations without recomputation:

| Condition violated | Correct approach | Resulting constant |
|---|---|---|
| Full information (cardinal scores available) | Threshold Rule (Section 6) | \(\approx 58\%\) success |
| Rejection possible (50% accept rate) | Propose from \(25\%\) onward | \(\approx 25\%\) success |
| Recall possible (50% recall-accept rate) | Look to \(61\%\), then leap or fall back | \(\approx 61\%\) success |
| \(n\) itself is unknown but uniformly distributed over \([1, n_{max}]\) | Look at first \(n/e^2\) (\(\approx 13.5\%\)), then take next best-yet | \(2/e^2 \approx 27\%\) success |
| Search may end at any step with probability \(p\) (unknown, possibly infinite horizon) | Look at first \(0.18/p\) candidates | \(\approx 23.6\%\) success |
| Payoff decays with search length (\(d^k\) after \(k\) views) | Threshold bounded by \(1/(1-d)\); for \(d\) near 1, look at first \(-0.4348/\log d\) candidates | strategy-dependent, often very short search |
| Goal is maximizing *average rank*, not best-or-nothing | Multi-threshold rule (thresholds increase over time), via backward induction | avg rank \(1\tfrac{7}{8}\) for \(n=4\) vs. \(2\tfrac{1}{2}\) random |
| Goal is maximizing *duration of ownership* of the best object | Look at first \(0.204n + 1.33\) candidates | N/A |
| Goal is maximizing duration of holding *a* best-yet (not necessarily global best) object | Look at first \(1/e^2 \approx 13.5\%\) | N/A |
| Goal is finding the *second-best* candidate | Pass over first half, then take next second-best-yet | \(25\%\) success (worse than best-seeking) |
| Payoff is \(+1\) for best, \(-1\) for any other, \(0\) for no pick | Different proportion via Sakaguchi's bilateral formula | N/A |
| Average reward for stopping at the best point is infinite (e.g., "triple or nothing," stakes always fully re-wagered) | **No optimal stopping rule exists** | undefined / always-continue leads to ruin |

**Hard invalidity condition (formal)**: an optimal stopping rule exists only if the expected reward for stopping at the best achievable point is finite. Games where the payoff grows geometrically in the number of rounds played (e.g., triple-or-nothing, or any utility-preserving analog such as "cube or nothing" under logarithmic utility) violate this condition; the average payoff over the stopping time is infinite, so no threshold or leap rule ever caps optimal behavior at a finite point, and the naive "always continue" strategy leads to eventual ruin. **Anti-pattern**: treating a diverging-expectation game as an optimal stopping problem at all; such problems require a different framework (e.g., fractional-bankroll rules such as Kelly betting) rather than a stopping rule.

---

## 9. Search-Cost Formulations (Continuous / Full-Information + Cost of Waiting)

Applies when: full information exists (objective value scale), the number of future offers is effectively unbounded (no fixed \(n\)), and each additional look costs something (time, money, opportunity cost) rather than simply risking a missed best option.

**Setup (house-selling problem)**: offers arrive one at a time, drawn from a known range; each rejected offer costs a fixed continuation cost \(c\) (e.g., cost of waiting for the next offer). Objective is no longer "find the single best" but "maximize expected net value" (price obtained minus cumulative waiting cost).

**Threshold derivation**: expressing offer price \(p\) and continuation cost \(c\) as fractions of the offer range (0 = bottom, 1 = top of range), the expected gain from continuing to search must exceed \(c\) to justify continuing:

\[
(1-p)\left(\frac{1-p}{2}\right) \ge c
\]

Solving for \(p\) gives the stopping threshold. Because the terms of this equation never depend on how long the search has already run, **the threshold is fixed once, before the search begins, and never changes** with elapsed time or bad luck.

**Behavioral consequences**:
- If waiting cost is negligible, the threshold approaches the top of the range (near-maximal selectivity).
- As waiting cost rises, the threshold falls (accept a wider range of offers).
- If waiting cost is \(\ge 1/2\) of the total offer range, the threshold collapses to the bottom of the range: accept the very first offer.
- **No recall, ever, even if permitted**: because the threshold never decreases over time, any previously rejected offer (which was, by construction, below the threshold when seen) can never become acceptable later. Recalling a past offer is provably never optimal in this formulation; unlike the classical secretary problem's recall variant, where recall is directly useful. Money and time already spent searching are sunk costs and must not influence the fixed threshold.

**Pseudocode**:
```
function cost_aware_threshold(offer_range: (low, high), cost_c_normalized: float) -> threshold:
    # solve (1 - p) * (1 - p) / 2 >= c  for p, using normalized [0,1] scale
    p = 1 - sqrt(2 * cost_c_normalized)
    return low + p * (high - low)

function house_selling(offers: stream, threshold: float) -> accepted_offer:
    for offer in offers:
        if offer >= threshold:
            return offer     # accept; never revisit rejected offers
    # if offers are finite and exhausted, this variant assumes an unbounded stream;
    # a finite, known-count version uses a lower (less conservative) threshold instead
```

**Finite-vs-infinite invariant**: if the number of remaining offers is known and finite (savings will run out, or interest is expected to stop after some point), the optimal threshold is *lower* (less selective) than in the infinite-offer case, and should decrease as the remaining opportunity count shrinks; this reintroduces some of the dynamic-threshold behavior from Section 6, layered on top of the cost-of-search logic.

---

## 10. Spatial / Duration Analog: The Parking Problem

Same mathematical family as Section 9, restated over distance instead of price, with a discrete occupancy parameter.

**Setup**: an unbounded sequence of parking spots at fixed spacing, each independently occupied with probability equal to the **occupancy rate** \(p\). Objective: minimize walking distance to a fixed destination.

**Rule**: Look-Then-Leap over distance; ignore all empty spots farther than a computed cutoff distance from the destination, then take the first empty spot found at or within that distance.

**Cutoff formula**:

\[
d^{*} = \left\lfloor \frac{-\log 2}{\log(1-p)} \right\rfloor
\]

spots from the destination, where \(p\) is the occupancy rate (probability any given spot is occupied).

**Invariant**: higher occupancy rate \(\to\) larger cutoff distance \(\to\) must start "seriously looking" farther from the destination. The relationship is highly nonlinear near \(p=1\): moving occupancy from 90% to 95% (a 5.5% relative increase) roughly doubles the expected search length.

**Anti-pattern (policy-level)**: treating high occupancy as evidence of efficient resource utilization; under this model, near-100% occupancy imposes large, hidden search costs (time, fuel) not captured by the occupancy metric alone. An occupancy rate around 85–90% is commonly cited as balancing utilization against search cost.

---

## 11. Duration / Unknown-Horizon and "Quit While Ahead" Adaptations

**Real-world time cost**: the classical secretary model has no intrinsic cost for the act of searching itself. When an implicit cost per observation is added (e.g., cost equal to some fraction of the value of the best possible outcome), the optimal look-phase boundary shortens correspondingly; observed human behavior (people leaping earlier than the theoretical 37% point, often around 30% or less) is consistent with searchers implicitly pricing in real time costs not present in the zero-order model. **This does not invalidate the model; it identifies a missing cost term that should be added to the objective function.**

**Burglar / accumulating-reward-with-ruin-risk problem** (a distinct stopping structure: repeated trials with a per-trial success probability \(q\) and average per-success gain \(m\), but total ruin on failure):

**Rule**: continue only while accumulated gains remain below a computed ceiling; stop once gains reach or exceed:

\[
\text{ceiling} = \frac{mq}{1-q}
\]

Equivalently, for a fixed per-trial gain (e.g., win \$1 per success, lose everything on failure with probability \(1-q\)), the expected optimal number of trials before stopping is approximately \(q/(1-q)\).

**Pseudocode**:
```
function burglar_stop(success_prob_q: float, mean_gain_m: float, accumulated: float) -> bool:
    ceiling = mean_gain_m * success_prob_q / (1 - success_prob_q)
    return accumulated >= ceiling   # True => stop now
```

**Invariant**: this is a *ruin-risk* stopping structure, distinct from the secretary-family "best-or-nothing" structure; the decision variable is accumulated value, not sequential rank, and the rule is a single static ceiling rather than a look/leap boundary.

**Unknown-horizon note**: when the total number of opportunities \(n\) is not fixed in advance, the correct family of rules replaces "fraction of \(n\)" cutoffs with cutoffs based on a stopping-probability parameter \(p\) per step, or on an assumed distribution over \(n\) (see Section 8 table, rows 4–5). A zero-order stopping policy must specify explicitly whether \(n\) is fixed-and-known, fixed-and-unknown (with a distributional assumption), or open-ended (stochastic termination) before a cutoff constant can be chosen.

---

## Compact Worked Algorithm (General-Purpose Optimal Stopping Selector)

Given a sequential decision problem, first classify it, then dispatch to the correct rule:

```
function classify_and_solve(problem):
    if payoff_structure == "best-or-nothing":
        if n_known_and_fixed:
            if information == "ordinal_only":
                if recall_allowed and rejection_prob == 0:
                    r = round(0.61 * n)          # look-to-61%, fallback recall
                elif rejection_prob > 0:
                    r = round(0.25 * n)           # propose early & often (rejection case)
                else:
                    r = round(n / e)              # classical 37% rule
                return look_then_leap(candidates, r)
            elif information == "cardinal_full":
                return threshold_rule(candidates, percentile_score)
        elif n_unknown_but_bounded_uniform:
            r = round(n_max / e**2)               # ~13.5% look phase, i.e. n_max / e^2
            return look_then_leap(candidates, r)
        elif n_unbounded_stochastic_stop(p):
            r = round(0.18 / p)
            return look_then_leap(candidates, r)
    elif payoff_structure == "cost_of_search" and information == "cardinal_full":
        threshold = cost_aware_threshold(offer_range, normalized_cost)
        return house_selling(offers, threshold)
    elif payoff_structure == "accumulate_with_ruin_risk":
        return burglar_stop(success_prob_q, mean_gain_m, accumulated)
    elif expected_reward_at_best_stop_is_infinite:
        raise NoOptimalStoppingRuleExists("switch to a bankroll-fraction framework, e.g. Kelly betting")
    else:
        raise UnclassifiedVariant("consult multi-threshold / average-rank / duration formulas")
```

**Inputs required before dispatch**: payoff structure (best-or-nothing, cost-of-search, ruin-risk, average-rank, duration), information type (ordinal-only vs. cardinal/full), horizon type (fixed-known, fixed-unknown-distributional, or open-ended stochastic), recall/rejection permissions, and (for cost-based variants) a per-step or per-offer cost normalized to the outcome scale.

**Output**: index or value of the option to accept, plus (where applicable) the numeric cutoff or threshold used.

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
| Ordinal/positional | Unbounded spatial sequence, occupancy \(p\) | No | No | Minimize distance | Parking Threshold | \(d^{*} = \lfloor -\log 2/\log(1-p)\rfloor\) | scenario-dependent |
| N/A | Repeated trials, ruin on failure | N/A | N/A | Accumulate then stop | Burglar Rule | ceiling \(= mq/(1-q)\) | scenario-dependent |
| N/A | Any | N/A | N/A | Reward diverges at best stopping point | **No rule exists** | undefined | undefined |

---

## Key Invariants Across All Variants

1. Every finite-\(n\), best-or-nothing, ordinal-information variant without recall or rejection converges to the same look/success constant \(1/e \approx 0.37\) as \(n \to \infty\); this constant is not a universal law of stopping problems but a signature of that specific assumption set.
2. Adding cardinal information strictly increases achievable success probability and collapses the two-phase Look-Then-Leap structure into a single monotonic Threshold Rule.
3. Facing rejection risk shortens the look/leap boundary (37% down to 25% in the worked case) and lowers achievable success probability; adding recall with imperfect recall-acceptance lengthens the boundary (37% up to 61% in the worked case) and raises achievable success probability. In the recall case, success probability happens to equal the boundary proportion numerically (both 61%), the same look/success symmetry seen in the classical 37% case; this is an emergent property of that specific parameterization, not a general law that holds for every recall or rejection probability.
4. Whenever a fixed per-step or per-offer cost enters the objective, the resulting threshold becomes cost-derived, is generally static (set once, not recalibrated by elapsed search), and forecloses recall as ever optimal.
5. A stopping rule requires that the expected payoff at the best conceivable stopping time be finite; unbounded-growth payoff structures admit no stopping rule and must be handled by a different mechanism entirely (e.g., fractional-stake rules).
