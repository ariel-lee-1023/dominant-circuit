---
name: dominant-circuit
description: "Master decision-mechanics router for choosing when to stop a search, how to trade off multiple objectives under certainty or uncertainty, and how to select or time actions in sequential/uncertain environments. Use when the user asks when to stop looking or searching, how to decide among finitely many alternatives with competing objectives, how to weigh tradeoffs or set scaling constants/utility weights, how to update beliefs with new evidence (Bayes/POMDP), how to pick an action under a Markov Decision Process or Bellman framework, or invokes phrases like optimal stopping, secretary problem, 37% rule, satisficing threshold, multiattribute utility, preferential/utility independence, expected utility, risk aversion, MDP, POMDP, belief update, value iteration, Q-learning, or Monte Carlo tree search. Not for open-ended brainstorming or single-attribute certainty comparisons with no search, tradeoff, or sequential/uncertainty structure."
---

# Dominant-Circuit

Master router over three zero-order decision-mechanics clusters. This file dispatches, it does not restate the math. Open the linked cluster file before computing.

## When to use

Use when a request has **decision structure**, not just a question:
- A search/queue of options must be stopped at some point ("when do I stop looking/interviewing/dating/selling/renting").
- Multiple competing objectives/attributes must be traded off into one ranking or score ("which alternative is best given cost, quality, risk...").
- An action must be chosen now that affects a future state under known/unknown dynamics, or beliefs must be updated from observations ("what should I do next," "update my belief," "plan a sequence of moves").

Not for single-criterion lookups, open-ended ideation, or anything with no explicit alternatives/objective/uncertainty structure.

## Which cluster for which job

| Job | Cluster | One-line trigger |
|---|---|---|
| Decide when to stop searching and commit to an option | [references/clusters/c01-optimal-stopping.md](references/clusters/c01-optimal-stopping.md) | "when do I stop looking," secretary problem, 37% rule, threshold rule, house-selling/parking, recall/rejection |
| Rank or score alternatives against several objectives/attributes, certain or uncertain | [references/clusters/c02-multiple-objectives.md](references/clusters/c02-multiple-objectives.md) | multiattribute utility, value function, preferential/utility independence, scaling constants, risk aversion, additive vs. multiplicative |
| Choose an action or plan over time under known/unknown dynamics, or update beliefs from evidence | [references/clusters/c03-sequential-decisions.md](references/clusters/c03-sequential-decisions.md) | MDP, POMDP, Bayes/belief update, Bellman equation, value iteration, Q-learning, MCTS |

If a request spans jobs (e.g., "stop searching once expected multiattribute utility falls below a threshold"), read all relevant clusters and compose per the Unified Pipeline below.

## Input contract (elicit or infer every field before computing)

1. **Horizon**: fixed known \(n\); fixed unknown with distribution (e.g. uniform on \([1,n_{max}]\)); open-ended/stochastic stop probability \(p\); finite-horizon sum; infinite-horizon discounted (\(\gamma\)) or average return.
2. **Feasible alternatives/states/actions**: set \(A\) (multi-objective case), or \(\mathcal{S}\), \(\mathcal{A}\) (sequential case), or the candidate stream (stopping case).
3. **Objective hierarchy and attribute ranges**: decomposition into attributes \(X_1,\ldots,X_n\), each with an explicit, recorded \([\text{worst},\text{best}]\) range spanned by the feasible alternatives.
4. **Subjective constraints/preferences**: preferential/utility independence assumptions (verified, not assumed), monotonicity direction per attribute, dominance pruning.
5. **Uncertainty models/prior/observations**: for stopping, ordinal-only vs. cardinal/full information; for sequential decisions, \(T\), \(R\), observation model \(O\) (POMDP), prior belief \(b_0\), observation stream.
6. **Search costs/recall/rejection**: per-look or per-offer cost; whether recall is possible and with what acceptance probability; whether an accepted offer can be rejected and with what probability.
7. **Risk attitude**: averse/neutral/prone, and constant/decreasing/increasing in attribute level (symmetric-lottery/fractile test, cluster 02 Sec. 4).
8. **Computational budget/tolerance**: exact finite-\(n\) enumeration vs. asymptotic approximation; iteration cap `k_max` or residual tolerance \(\delta\); MCTS simulations \(m\) or search depth \(d\); consistency-audit tolerance.

If any field is missing, run the Socratic elicitation loop below before computing; never silently default to the classical 37%-style assumption set.

## Output contract (every answer must report all applicable fields)

1. **Chosen action/stop decision**: the index/value to accept, or the action \(a^{*}\) to execute now.
2. **Unified zero-order formula used**: the exact named formula (e.g., Threshold Rule, additive value function, Bellman optimality equation), with cluster and section cited.
3. **Belief/value/threshold**: current belief vector \(b\) (if applicable), the value \(U(s)\), \(Q(s,a)\), or \(P_n(r)\) achieved, and the numeric threshold/cutoff used.
4. **Assumptions**: full input-contract values assumed or elicited, stated explicitly, so the answer is auditable and non-transferable to a different assumption set.
5. **Sensitivity**: how the decision changes if a stated assumption (horizon, recall/rejection probability, risk attitude, discount \(\gamma\)) is perturbed; flag fragility.
6. **Audit failures**: any validation invariant (below) that failed, with the specific residual and implicated response/quantity.

## Hard preconditions (check before dispatch; violating these invalidates the corresponding cluster's formulas)

- **Cluster 01**: a stopping rule exists only if the expected payoff at the best conceivable stopping point is finite; diverging-expectation games (e.g., triple-or-nothing) have no optimal stopping rule and must be handled by a different framework (e.g., fractional-bankroll rules).
- **Cluster 02**: the additive value/utility form requires mutual (or, for \(n=3\), pairwise) preferential or utility independence, verified by an explicit indifference test, not assumed for simplicity. Scaling constants are only interpretable jointly with the attribute ranges they were assessed against.
- **Cluster 03**: the Markov assumption must hold (next state depends only on current state and action); Bellman-backup convergence requires \(\gamma \in [0,1)\) and bounded rewards; belief updates require a well-defined observation model and must reset to uniform on zero-likelihood evidence rather than divide by zero.

## Unified pipeline

1. **Classify.** Identify which job(s) apply. Determine payoff structure (best-or-nothing, net-value-minus-cost, ruin-risk, multiattribute score, cumulative discounted return).
2. **Elicit.** Fill every input-contract field via the Socratic loop. Record assumptions verbatim; never silently substitute the classical/simplified case.
3. **Verify preconditions.** Check hard preconditions for every cluster invoked. Block computation and surface the specific missing verification if unmet (independence not tested, horizon type unspecified, etc.).
4. **Select formula.** Dispatch to the exact named rule for the elicited assumption set (each cluster's decision table/dispatch pseudocode). Never reuse a constant (37%, 0.61, 58%) calibrated for a different assumption set.
5. **Compute.** Run the corresponding pseudocode (finite-\(n\) argmax, additive/multiplicative utility, Bayes/belief update, Bellman backup, or online planner) at the declared computational budget.
6. **Audit.** Run applicable validation invariants. Surface any residual outside tolerance as an audit failure, not a silently accepted answer.
7. **Report.** Emit the full output contract, including sensitivity to the assumptions most likely to be wrong or contested.
8. **Iterate on inconsistency.** If elicited responses conflict, or a residual fails, return to Step 2 with the specific conflict surfaced to the user, per each cluster's consistency-loop mechanics.

## Minimal Socratic elicitation loop

Ask only what is missing, in this order, stopping once the job is fully specified:

1. "Is there a queue/stream of options to search through, or a fixed set already in hand?" (c01 vs. c02/c03)
2. "Do you know the total number of options/time \(n\), or is it open-ended?" (horizon)
3. "Can you compare options only relatively as they arrive, or do you have an absolute score for each?" (ordinal vs. cardinal, c01)
4. "Once you pass on an option, can you revisit it? Can an accepted option later say no?" (recall/rejection)
5. "What attributes matter, and what is the worst-to-best range you care about for each?" (attribute hierarchy/ranges, c02)
6. "If forced to trade a sure outcome against a 50-50 gamble of equal expected value, which would you pick?" (risk attitude)
7. "Is the environment's response to actions known (transition model), or must it be tracked as a belief?" (MDP vs. POMDP, c03)
8. "How exact must this be: closed-form/asymptotic, or exact finite computation within a stated tolerance/budget?" (compute budget)

## Core formulas (exact, by cluster)

**Multiattribute value/utility (cluster 02).** Additive, valid only under verified mutual/pairwise preferential (certainty) or utility (uncertainty) independence, weights summing to 1:
\[
v(x_1,\ldots,x_n) = \sum_{i=1}^n \lambda_i v_i(x_i), \qquad u(x_1,\ldots,x_n) = \sum_{i=1}^n k_i u_i(x_i), \qquad \sum_i k_i = 1.
\]
Multiplicative, when mutual utility independence holds but \(\sum_i k_i \ne 1\):
\[
1 + k\,u(x) = \prod_{i=1}^n \bigl(1 + k\,k_i\,u_i(x_i)\bigr), \qquad 1+k=\prod_{i=1}^n(1+k k_i).
\]
Additive is the special case \(k=0\) (i.e. \(\sum_i k_i = 1\)) of the multiplicative form, not a separately-derived rule.

**Bayes update / POMDP belief update (cluster 03).**
\[
P(x\mid y) = \frac{P(y\mid x)P(x)}{P(y)}, \qquad b'(s') \propto O(o\mid a,s') \sum_s T(s'\mid s,a)\,b(s).
\]

**Bellman action selection (cluster 03).**
\[
Q(s,a) = R(s,a) + \gamma \sum_{s'} T(s'\mid s,a)\,U(s'), \qquad a^{*} = \arg\max_a Q(s,a), \qquad U^{*}(s) = \max_a Q(s,a).
\]

**Stop iff stop value \(\ge\) continuation value (cluster 01, general criterion underlying every stopping rule here).** At any decision point, stop (accept/leap) iff
\[
V_{\text{stop}} \ge V_{\text{continue}},
\]
where \(V_{\text{stop}}\) is the value of accepting now and \(V_{\text{continue}}\) is the expected value of continuing under the optimal future policy. Every rule in cluster 01 (Look-Then-Leap, Threshold Rule, cost-aware threshold, burglar ceiling) is this one criterion specialized to a payoff structure and information condition. **The 37% constant is what this criterion reduces to only under the classical secretary assumption set** (fixed known \(n\), ordinal-only, no recall, no rejection, best-or-nothing payoff); it is a special case, not the general formula. Change one assumption and the same criterion yields a different constant (58% full information, 25% rejection risk, 61% recall, or none at all under diverging payoffs); see cluster 01 Sec. 8.

## Compact orchestration (Python-computable)

```python
def dispatch(job, contract):
    # job in {'stopping','multiobjective','sequential'}; contract = filled input-contract dict
    verify_preconditions(job, contract)                     # hard preconditions above
    if job == "stopping":
        rule, params = select_stopping_rule(contract)       # c01 classify_and_solve
        decision = rule(**params)
    elif job == "multiobjective":
        assert independence_verified(contract)              # c02 Sec 3.4/5.1
        additive = sum(contract["k_i"]) == 1
        decision = additive_value(**contract) if additive else multiplicative_utility(**contract)  # c02 Sec 7.4
    elif job == "sequential":
        if contract.get("belief") is not None:
            contract["belief"] = belief_update(contract["belief"], contract["model"],
                                                contract["action"], contract["observation"])  # c03 Sec 9
            decision = belief_greedy_action(contract["model"], contract["U_belief_fn"], contract["belief"])
        else:
            decision = greedy_policy(contract["mdp"], contract["U"])(contract["state"])
    audit = run_validation_invariants(job, contract, decision)
    return {"decision": decision, "assumptions": contract, "audit": audit}
```

## Validation invariants (cross-cluster)

1. **Assumption-set match.** The constant/rule dispatched must correspond exactly to the elicited horizon/information/recall/rejection combination; reusing 37%, 58%, 61%, or 25% outside their calibrated assumption set is an audit failure.
2. **Normalization.** Every probability, belief, or component value/utility function must satisfy its stated normalization (\(\sum=1\), \(v(\text{worst})=0\), \(v(\text{best})=1\)) before use downstream.
3. **Independence verified, not assumed.** No additive or multiplicative multiattribute form may be used without a recorded, verified independence test (cluster 02 flip test or equivalent).
4. **Bellman fixed point.** After convergence, \(U(s) = \max_a Q(s,a)\) must hold to within declared tolerance \(\delta\); Bellman residuals must shrink by a factor no worse than \(\gamma\) per sweep.
5. **Range-fixed weights.** No scaling constant \(k_i\)/\(\lambda_i\) may be recorded without an attached, explicit attribute range; reusing one elicited under a different range is invalid.
6. **Finite-expectation precondition.** No stopping rule may be applied to a payoff structure with diverging expected value at the best stopping point.
7. **Overdetermination.** Elicitation must gather more indifference/trade-off equations than free parameters so inconsistency is detectable, not just assumed away.

## Anti-cargo-cult rules

- Never state "37%" as a universal answer to "when should I stop." It is the exact limit of \(P_n(r)\) under one specific assumption set (fixed known \(n\), ordinal-only, no recall, no rejection, best-or-nothing); state the assumption set alongside the number, every time.
- Never label a scaling constant \(k_i\) as an "importance weight" without citing the attribute range it was assessed against.
- Never adopt the additive multiattribute form because it is simpler; adopt it only after the independence test passes.
- Never treat an inconsistent elicitation response as noise to average away; surface it to the user and re-elicit.
- Never skip dominance screening before running full preference elicitation on a candidate set.
- Never apply a Bellman/MDP method to a non-Markov process without first re-deriving or augmenting the state to restore the Markov property.
- Never report a decision without its audit results; a passing computation with a failing invariant is not a valid answer.
