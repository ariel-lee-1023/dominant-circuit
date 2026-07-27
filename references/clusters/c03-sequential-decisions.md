# Cluster C03: Sequential Decisions

Source: *Algorithms for Decision Making* (Kochenderfer, Wheeler, et al.), representation, decision-network, exact MDP solution, online planning, model-free, and belief-state planning chapters. All mechanisms below are zero-order (fully specified, computable) restatements of the book's formalism, not summaries of prose.

## 1. Probability and Bayes Update

**Object.** A degree of belief over a proposition is represented by a probability \(P\) satisfying the standard axioms: \(0 \le P(A) \le 1\), \(P(A) = 1\) if \(A\) is certain, and for a discrete variable \(X\) over \(1{:}n\),
\[
\sum_{i=1}^n P(X = i) = 1, \qquad 0 \le P(X = i) \le 1 .
\]

**Conditional probability and total probability.** For evidence \(y\),
\[
P(x \mid y) = \frac{P(x, y)}{P(y)}, \qquad \sum_x P(x \mid y) = 1,
\]
\[
P(x) = \sum_y P(x \mid y) P(y).
\]

**Bayes' rule.**
\[
P(x \mid y) = \frac{P(y \mid x) P(x)}{P(y)}.
\]
- **Inputs:** a likelihood \(P(y\mid x)\), a prior \(P(x)\), and a normalizer \(P(y) = \sum_x P(y\mid x)P(x)\) (or an integral in the continuous case).
- **Output:** the posterior \(P(x\mid y)\).
- **Failure mode:** if \(P(y) = 0\) for the observed \(y\), the update is undefined; in implementation this is handled by falling back to a uniform (or prior) distribution rather than dividing by zero.

**Bayesian networks.** A Bayesian network factors a joint distribution over variables \(X_{1:n}\) as a product of conditionals given each node's parents, via the chain rule:
\[
P(x_{1:n}) = \prod_{i=1}^n P\bigl(x_i \mid \mathrm{parents}(X_i)\bigr).
\]
- **Inputs:** a directed acyclic graph over variables and a conditional probability table (CPT) or conditional density per node.
- **Output:** the joint distribution, and via inference algorithms (variable elimination, sampling), any marginal or conditional query.
- **Constraint:** the graph must be acyclic; conditional independence is encoded by missing edges.

Pseudocode for a discrete Bayesian network joint query:
```
def bn_joint_probability(bn, assignment):
    # bn.vars: ordered variables; bn.factors[i]: CPT for var i given its parents
    # assignment: dict var -> value, fully specified
    p = 1.0
    for i, var in enumerate(bn.vars):
        parent_vals = tuple(assignment[p] for p in bn.parents[i])
        p *= bn.factors[i][(assignment[var],) + parent_vals]
    return p

def bayes_update(prior, likelihood_fn, y):
    # prior: dict x -> P(x); likelihood_fn: (x, y) -> P(y|x)
    unnorm = {x: likelihood_fn(x, y) * prior[x] for x in prior}
    z = sum(unnorm.values())
    if z == 0.0:
        return dict(prior)  # failure fallback: no update
    return {x: v / z for x, v in unnorm.items()}
```

## 2. Decision Networks and Maximum Expected Utility

**Object.** A decision network (influence diagram) generalizes a Bayesian network with three node types: chance nodes (circles, random variables), action nodes (squares, decision variables), and utility nodes (diamonds, no children). Edges are conditional (into chance nodes), informational (into action nodes, denoting what is known when the decision is made), or functional (into utility nodes). The graph must remain acyclic.

**Maximum expected utility (MEU) principle.** Given a probabilistic model \(P(s' \mid o, a)\) over resulting state \(s'\) conditioned on observation \(o\) and action \(a\), and a utility function \(U(s')\), the expected utility of action \(a\) given \(o\) is
\[
EU(a \mid o) = \sum_{s'} P(s' \mid a, o)\, U(s').
\]
A rational agent chooses
\[
a^{*} = \arg\max_{a} EU(a \mid o).
\]
Total utility for an action equals the sum of values at all utility nodes reachable from it.

- **Inputs:** state/observation/action spaces, conditional model \(P(s'\mid o,a)\), utility function \(U\).
- **Output:** the optimal action \(a^{*}\) and its expected utility.
- **Failure mode:** if the utility or probability model is misspecified (e.g., wrong conditional independencies assumed), MEU selects an action that is optimal under the wrong model, not the true environment.

```
def expected_utility(action, obs, transition_model, utility_fn, states):
    return sum(transition_model(s_next, action, obs) * utility_fn(s_next)
               for s_next in states)

def meu_action(actions, obs, transition_model, utility_fn, states):
    return max(actions, key=lambda a: expected_utility(a, obs, transition_model, utility_fn, states))
```

This MEU computation over a single-shot decision network is the base case that sequential decision making (MDPs, POMDPs) extends over multiple time steps.

## 3. Markov Decision Process (MDP): Tuple and Markov Constraint

**Definition.** An MDP is the tuple
\[
(\mathcal{S}, \mathcal{A}, T, R, \gamma)
\]
where:
- \(\mathcal{S}\): state space (finite or infinite).
- \(\mathcal{A}\): action space.
- \(T(s' \mid s, a)\): transition model, the probability of moving to \(s'\) given current state \(s\) and action \(a\).
- \(R(s, a)\): expected reward for executing \(a\) in \(s\); if reward depends on the outcome state, \(R(s,a) = \sum_{s'} T(s'\mid s,a)\, R(s,a,s')\).
- \(\gamma \in [0,1)\): discount factor (for infinite horizon).

**Markov assumption (constraint).** The next state depends only on the current state and action, not on any earlier history:
\[
P(s_{t+1} \mid s_{1:t}, a_{1:t}) = T(s_{t+1} \mid s_t, a_t).
\]
Stationary MDPs additionally require that \(T\) and \(R\) do not vary with time \(t\).

**Policy.** A (stationary, deterministic) policy \(\pi: \mathcal{S} \to \mathcal{A}\) selects an action from the current state. Stochastic policies specify \(\pi(a \mid s)\), the probability of selecting \(a\) in \(s\).

```
class MDP:
    def __init__(self, S, A, T, R, gamma):
        self.S, self.A, self.T, self.R, self.gamma = S, A, T, R, gamma

    def sample_transition_reward(self, s, a, rng):
        # TR(s, a) -> (s_next, r); implements T and R generatively
        s_next = rng.choices(self.S, weights=[self.T(sp, s, a) for sp in self.S])[0]
        r = self.R(s, a)
        return s_next, r
```

## 4. Return: Finite and Infinite Horizon

**Finite horizon** (\(n\) decisions): the utility of a reward sequence \(r_{1:n}\) is the additively decomposed return
\[
\sum_{t=1}^n r_t.
\]

**Infinite horizon, discounted return:**
\[
\sum_{t=1}^{\infty} \gamma^{t-1} r_t, \qquad 0 \le \gamma < 1.
\]
Discounting guarantees a finite utility for bounded rewards and encodes a time preference (present reward valued more than future reward).

**Infinite horizon, average return** (alternative, avoids choosing \(\gamma\)):
\[
\lim_{n \to \infty} \frac{1}{n} \sum_{t=1}^n r_t.
\]
The discounted formulation is computationally preferred because it yields a contraction mapping (see Section 6).

```
def discounted_return(rewards, gamma):
    return sum((gamma ** t) * r for t, r in enumerate(rewards))
```

## 5. Value Functions, Bellman Expectation Equation, Policy Evaluation

**Value function.** \(U^{\pi}(s)\) is the expected discounted return of executing policy \(\pi\) starting at state \(s\).

**Lookahead equation** (one-step expansion using a current value estimate \(U_k\)):
\[
U_{k+1}^{\pi}(s) = R(s, \pi(s)) + \gamma \sum_{s'} T(s' \mid s, \pi(s))\, U_k^{\pi}(s').
\]

**Bellman expectation equation** (fixed point at convergence):
\[
U^{\pi}(s) = R(s, \pi(s)) + \gamma \sum_{s'} T(s' \mid s, \pi(s))\, U^{\pi}(s').
\]

**Convergence.** Iterating the lookahead update is guaranteed to converge to \(U^{\pi}\) because the update is a contraction mapping in the sup-norm (with modulus \(\gamma\)). Convergence can also be obtained exactly (non-iteratively) by solving the linear system
\[
U^{\pi} = R^{\pi} + \gamma T^{\pi} U^{\pi} \;\Longrightarrow\; U^{\pi} = (I - \gamma T^{\pi})^{-1} R^{\pi},
\]
at cost \(O(|\mathcal{S}|^3)\) for the matrix solve, versus \(O(|\mathcal{S}|^2 |\mathcal{A}|)\) or \(O(|\mathcal{S}|^2)\) per sweep for iterative evaluation (policy fixed, so no max over actions).

- **Inputs:** MDP \((\mathcal{S}, \mathcal{A}, T, R, \gamma)\), a fixed policy \(\pi\), stopping criterion (`k_max` iterations, or residual tolerance).
- **Output:** \(U^{\pi}(s)\) for all \(s\).
- **Stopping criterion:** either a fixed iteration budget `k_max`, or when the Bellman residual \(\lVert U_{k+1} - U_k\rVert_\infty\) drops below a threshold \(\delta\).

```
def lookahead(mdp, U, s, a):
    return mdp.R(s, a) + mdp.gamma * sum(mdp.T(sp, s, a) * U[sp] for sp in mdp.S)

def iterative_policy_evaluation(mdp, pi, k_max):
    U = {s: 0.0 for s in mdp.S}
    for _ in range(k_max):
        U = {s: lookahead(mdp, U, s, pi(s)) for s in mdp.S}
    return U

def exact_policy_evaluation(mdp, pi):
    # Solve (I - gamma T_pi) U = R_pi directly; O(|S|^3)
    # Row i must index s, column j must index s', so Tp[i][j] = T(s'=S[j] | s=S[i], pi(S[i]))
    import numpy as np
    S = list(mdp.S)
    n = len(S)
    idx = {s: i for i, s in enumerate(S)}
    Tp = np.array([[mdp.T(sp, s, pi(s)) for sp in S] for s in S])  # outer loop = row = s, inner loop = column = s'
    Rp = np.array([mdp.R(s, pi(s)) for s in S])
    U = np.linalg.solve(np.eye(n) - mdp.gamma * Tp, Rp)
    return {s: U[idx[s]] for s in S}
```

## 6. Bellman Optimality Equation, Q-Function, Value Iteration

**Greedy policy extraction.** Given any value function \(U\) (optimal or not),
\[
\pi(s) = \arg\max_{a} \Bigl( R(s,a) + \gamma \sum_{s'} T(s'\mid s,a)\, U(s') \Bigr).
\]
If \(U = U^{*}\), the extracted policy is optimal.

**Action-value function (Q-function).**
\[
Q(s,a) = R(s,a) + \gamma \sum_{s'} T(s'\mid s,a)\, U(s'),
\]
with
\[
U(s) = \max_a Q(s,a), \qquad \pi(s) = \arg\max_a Q(s,a).
\]
Storing \(Q\) costs \(O(|\mathcal{S}| \times |\mathcal{A}|)\) versus \(O(|\mathcal{S}|)\) for \(U\), but avoids needing \(T\) and \(R\) at action-selection time.

**Advantage function.** \(A(s,a) = Q(s,a) - U(s)\); zero for greedy actions, negative otherwise.

**Bellman backup (Bellman update).**
\[
U_{k+1}(s) = \max_{a} \Bigl( R(s,a) + \gamma \sum_{s'} T(s'\mid s,a)\, U_k(s') \Bigr).
\]

**Bellman optimality equation** (fixed point of the backup):
\[
U^{*}(s) = \max_{a} \Bigl( R(s,a) + \gamma \sum_{s'} T(s'\mid s,a)\, U^{*}(s') \Bigr).
\]

**Value iteration.** Repeated application of the Bellman backup from any bounded initial \(U\) (commonly \(U_0(s)=0\)) converges to \(U^{*}\) because the backup is a contraction mapping.

- **Stopping criterion:** fixed `k_max`, or Bellman residual \(\lVert U_{k+1}-U_k\rVert_\infty < \delta\). A residual below \(\delta\) bounds the value error at \(\varepsilon = \delta\gamma/(1-\gamma)\), and the resulting policy loss is bounded by \(2\varepsilon\gamma/(1-\gamma)\). Discount factors near 1 inflate this error and slow convergence.
- **Computational constraint:** each sweep costs \(O(|\mathcal{S}|^2 |\mathcal{A}|)\) for tabular transition models.

**Policy iteration** (alternative exact method): alternate full policy evaluation with greedy policy improvement until the policy is unchanged. Guaranteed to converge in a finite number of steps (finitely many deterministic policies, monotonic improvement), but each iteration is more expensive than one value-iteration sweep. Modified policy iteration truncates the evaluation step to a fixed number of sweeps; using exactly one sweep per improvement step reduces to value iteration.

```
def backup(mdp, U, s):
    return max(lookahead(mdp, U, s, a) for a in mdp.A)

def value_iteration(mdp, k_max=None, tol=None):
    U = {s: 0.0 for s in mdp.S}
    k = 0
    while True:
        U_new = {s: backup(mdp, U, s) for s in mdp.S}
        residual = max(abs(U_new[s] - U[s]) for s in mdp.S)
        U = U_new
        k += 1
        if (k_max is not None and k >= k_max) or (tol is not None and residual < tol):
            break
    return U

def greedy_policy(mdp, U):
    def pi(s):
        return max(mdp.A, key=lambda a: lookahead(mdp, U, s, a))
    return pi

def policy_iteration(mdp, pi0, k_max):
    pi = pi0
    for _ in range(k_max):
        U = exact_policy_evaluation(mdp, pi)
        pi_next = greedy_policy(mdp, U)
        if all(pi_next(s) == pi(s) for s in mdp.S):
            break
        pi = pi_next
    return pi
```

**Failure modes for exact MDP methods:** exponential blow-up in the number of policies to enumerate implicitly (mitigated by dynamic programming, not brute force); intractability when \(|\mathcal{S}|\) or \(|\mathcal{A}|\) is large or continuous (motivating approximate value functions, not covered here except as a boundary condition); slow convergence under \(\gamma\) close to 1.

## 7. Online Planning and Replanning

**Receding horizon planning.** Plan from the current state to a fixed depth \(d\), execute only the first action, transition to the resulting state, then replan from scratch. This is the general scheme for all online methods described here.

- **Inputs:** current state \(s\), depth \(d\), a way to evaluate or bound value beyond depth \(d\) (a rollout policy, a heuristic \(U\), or zero).
- **Output:** one action to execute; the plan is discarded and recomputed at the next state.
- **Tradeoff:** deeper \(d\) costs more computation but can be necessary to detect distant goals or hazards; frequent replanning can compensate for shallow depth in some problems.

**Forward search.** Expand all reachable state-action sequences to depth \(d\), forming a search tree, and back up values with the Bellman backup at each level; at depth \(d\), bootstrap with a value estimate \(U(s)\) (often \(0\) if planning only to the horizon).
\[
\text{Worst-case complexity: } O\bigl((|\mathcal{S}| \times |\mathcal{A}|)^d\bigr).
\]

```
def forward_search(mdp, s, d, U_leaf):
    if d <= 0:
        return None, U_leaf(s)
    best_a, best_u = None, float('-inf')
    for a in mdp.A:
        u = mdp.R(s, a)
        for sp in mdp.S:
            p = mdp.T(sp, s, a)
            if p == 0.0:
                continue
            _, u_next = forward_search(mdp, sp, d - 1, U_leaf)
            u += mdp.gamma * p * u_next
        if u > best_u:
            best_a, best_u = a, u
    return best_a, best_u
```

**Lookahead with rollouts.** Replace the exact backup with Monte Carlo simulation using a rollout policy \(\pi_{\text{rollout}}\) and a generative model \(s' \sim T(\cdot\mid s,a)\); running \(m\) simulations per action-state pair costs \(O(m \times |\mathcal{A}| \times |\mathcal{S}| \times d)\) and trades exactness for tractability on large or continuous spaces. Optimality is not guaranteed; this is an approximate policy-improvement step.

**Sparse sampling.** At each state, draw \(m\) successor samples per action from the generative model rather than enumerating all successors, recursing to depth \(d\):
```
def sparse_sampling(mdp, s, d, m, U_leaf, rng):
    if d <= 0:
        return None, U_leaf(s)
    best_a, best_u = None, float('-inf')
    for a in mdp.A:
        u = 0.0
        for _ in range(m):
            sp, r = mdp.sample_transition_reward(s, a, rng)
            _, u_next = sparse_sampling(mdp, sp, d - 1, m, U_leaf, rng)
            u += (r + mdp.gamma * u_next) / m
        if u > best_u:
            best_a, best_u = a, u
    return best_a, best_u
```

**Monte Carlo tree search (MCTS).** Runs \(m\) simulations from the current state, maintaining visit counts \(N(s,a)\) and action-value estimates \(Q(s,a)\); actions during simulation are chosen by the UCB1 exploration rule
\[
\arg\max_{a}\; Q(s,a) + c \sqrt{\frac{\log N(s)}{N(s,a)}}, \qquad N(s) = \sum_a N(s,a),
\]
where \(c\) is an exploration constant and the bonus is defined as \(\infty\) when \(N(s,a)=0\). After \(m\) simulations, the action executed is \(\arg\max_a Q(s,a)\). Unvisited states are initialized with \(N(s,\cdot)=0\), \(Q(s,\cdot)=0\) (or prior estimates), and their value is bootstrapped via rollout.

```
import math

def ucb1_action(Q, N, s, actions, c):
    Ns = sum(N.get((s, a), 0) for a in actions)
    def score(a):
        Nsa = N.get((s, a), 0)
        if Nsa == 0:
            return float('inf')
        # Q(s,a) + c * sqrt(log(N(s)) / N(s,a)); guard Ns <= 1 so log(Ns) is not negative/undefined
        log_Ns = math.log(Ns) if Ns > 1 else 0.0
        return Q.get((s, a), 0.0) + c * math.sqrt(log_Ns / Nsa)
    return max(actions, key=score)
```

**Online replanning invariant.** Because online methods recompute a plan at every visited state, none of the intermediate plan structure needs to be globally consistent with future replans; only the single executed action from the current planning episode is trusted. Failure mode: if the depth/sample budget is insufficient relative to problem structure (e.g., sparse rewards far beyond the horizon), the online planner behaves myopically or fails to detect distant hazards, as with the collision-avoidance horizon example where shallow depth compromised safety.

## 8. Model Learning and Q-Learning (as needed)

When \(T\) and \(R\) are unknown, the Bellman expectation identity for the Q-function,
\[
Q(s,a) = R(s,a) + \gamma \sum_{s'} T(s'\mid s,a) \max_{a'} Q(s',a') = \mathbb{E}_{r,s'}\bigl[r + \gamma \max_{a'} Q(s',a')\bigr],
\]
motivates a model-free, sample-based incremental update (Q-learning) using only observed transitions \((s,a,r,s')\):
\[
Q(s,a) \leftarrow Q(s,a) + \alpha \Bigl( r + \gamma \max_{a'} Q(s',a') - Q(s,a) \Bigr),
\]
where \(\alpha\) is a learning rate. Convergence of the incremental mean estimate underlying this rule requires a learning-rate schedule that decays appropriately (too fast: convergence is slow; too slow, or constant \(\alpha\): the estimate keeps fluctuating and does not converge to a point). An exploration policy (e.g., \(\epsilon\)-greedy or softmax) is required over the course of learning so that all relevant \((s,a)\) pairs are visited; without exploration, \(Q\) cannot be guaranteed to converge to \(Q^{*}\).

```
def q_learning_update(Q, s, a, r, s_next, actions, alpha, gamma):
    best_next = max(Q.get((s_next, ap), 0.0) for ap in actions)
    td_target = r + gamma * best_next
    Q[(s, a)] = Q.get((s, a), 0.0) + alpha * (td_target - Q.get((s, a), 0.0))
    return Q
```

Model-based alternatives (maximum-likelihood transition/reward estimation from counts, then planning against the estimated model) are used when sample efficiency matters more than avoiding an explicit model; this is mentioned here only as the boundary case motivating Q-learning, per the zero-order scope of this cluster.

## 9. Uncertainty over State: POMDP, Observation Model, Belief Update

**POMDP tuple.**
\[
(\mathcal{S}, \mathcal{A}, \mathcal{O}, T, R, O, \gamma)
\]
extending the MDP with an observation space \(\mathcal{O}\) and observation model \(O(o \mid a, s')\), the probability (or density) of observing \(o\) after taking action \(a\) and transitioning to \(s'\). The agent never directly observes \(s\).

**Belief.** A belief \(b\) is a probability distribution over \(\mathcal{S}\), i.e., a vector satisfying
\[
b(s) \ge 0 \ \text{for all } s, \qquad \sum_s b(s) = 1,
\]
or in vector notation \(b \ge 0\), \(\mathbf{1}^\top b = 1\). The belief space \(\mathcal{B}\) is the probability simplex over \(\mathcal{S}\).

**Recursive Bayesian belief update.** Given prior belief \(b\), action \(a\), and new observation \(o\), the posterior belief is derived from the independence structure of the POMDP dynamic decision network:
\[
b'(s') = P(s' \mid b, a, o) \;\propto\; O(o \mid a, s') \sum_{s} T(s' \mid s, a)\, b(s).
\]
The normalizing constant is \(\sum_{s'} O(o\mid a,s') \sum_s T(s'\mid s,a) b(s)\).

- **Inputs:** prior belief vector \(b\), action \(a\), observation \(o\), transition model \(T\), observation model \(O\).
- **Output:** posterior belief vector \(b'\), normalized to sum to 1.
- **Failure mode:** if the observation \(o\) has zero likelihood under every reachable successor state (an inconsistent observation given the model), the unnormalized posterior is identically zero; the standard fallback is to reset to a uniform belief rather than divide by zero.
- **Continuous case:** the update generalizes to an integral, \(b'(s') \propto O(o\mid a,s') \int T(s'\mid s,a) b(s)\, ds\); under linear-Gaussian transition/observation models and a Gaussian belief, this integral is solved exactly by the Kalman filter predict/update equations, noted here only as the continuous-state analogue.

```
def belief_update(b, mdp_pomdp, a, o):
    S = list(mdp_pomdp.S)
    b_next = {}
    for sp in S:
        po = mdp_pomdp.O(o, a, sp)  # observation model O(o | a, s'), argument order (o, a, s')
        b_next[sp] = po * sum(mdp_pomdp.T(sp, s, a) * b[s] for s in S)
    z = sum(b_next.values())
    if z == 0.0:
        n = len(S)
        return {s: 1.0 / n for s in S}  # failure fallback: uniform reset
    return {sp: v / z for sp, v in b_next.items()}
```

## 10. Belief-State MDP and Belief-State Bellman Backup

**Belief-state MDP.** Any POMDP can be reframed as an MDP over the continuous state space \(\mathcal{B}\) (all beliefs), with the same action space \(\mathcal{A}\), reward
\[
R(b,a) = \sum_s R(s,a)\, b(s),
\]
and belief-transition model
\[
T(b' \mid b, a) = \sum_{o} \mathbb{1}\bigl[b' = \mathrm{Update}(b,a,o)\bigr] \sum_{s'} O(o \mid a, s') \sum_s T(s'\mid s,a)\, b(s),
\]
i.e., the probability of landing on belief \(b'\) equals the probability of the observation \(o\) that deterministically produces \(b'\) via the belief update.

**Observation likelihood given belief and action** (needed for one-step lookahead):
\[
P(o \mid b, a) = \sum_{s} P(o \mid s, a)\, b(s), \qquad P(o \mid s, a) = \sum_{s'} T(s' \mid s, a)\, O(o \mid s', a).
\]

**Alpha vectors.** A conditional plan \(\pi\)'s expected utility from state \(s\) is
\[
U^{\pi}(s) = R(s,\pi()) + \gamma \sum_{s'} T(s'\mid s,\pi()) \sum_o O(o\mid \pi(), s')\, U^{\pi(o)}(s'),
\]
recursively evaluated over the plan tree with leaves at the planning horizon. Collecting \(U^{\pi}(s)\) over all \(s\) into a vector \(\alpha^{\pi}\) gives
\[
U^{\pi}(b) = \sum_s b(s)\, U^{\pi}(s) = (\alpha^{\pi})^\top b,
\]
so each conditional plan induces a hyperplane over belief space. The optimal value function is the upper envelope of these hyperplanes,
\[
U^{*}(b) = \max_{\pi} (\alpha^{\pi})^\top b,
\]
which is piecewise-linear and convex in \(b\). A policy is represented as a set of action-labeled alpha vectors \(\Gamma\); executing it means updating the belief and selecting the action of the vector \(\alpha \in \Gamma\) maximizing \(\alpha^\top b\) at the current belief.

**One-step lookahead action-value at a belief (belief-state Q-function):**
\[
Q(b,a) = R(b,a) + \gamma \sum_{o} P(o\mid b,a)\, U\bigl(\mathrm{Update}(b,a,o)\bigr),
\]
\[
\pi(b) = \arg\max_a Q(b,a).
\]

**Belief-state Bellman backup (POMDP value iteration).** Starting from one-step plans with alpha vectors \(\alpha_a = [R(s,a)]_{s}\) for each \(a\), iteratively:
1. **Expand:** form all \((|\Gamma_{k-1}| \times |\mathcal{O}|)\)-way combinations of action \(a\) with a subplan (from the previous horizon's dominating set) per observation \(o\), computing the new alpha vector for each combination via the plan-evaluation recursion above.
2. **Prune:** discard any alpha vector that is dominated everywhere in belief space, i.e., for which no belief \(b\) exists with \(\alpha^\top b\) strictly greatest among the retained set. Domination is checked by solving the linear program
\[
\max_{\delta, b} \delta \quad \text{s.t.} \quad b \ge 0,\ \mathbf{1}^\top b = 1,\ \alpha^\top b \ge {\alpha'}^\top b + \delta \ \text{for all } \alpha' \in \Gamma.
\]
If the optimal \(\delta \le 0\), \(\alpha\) is dominated and removed.
3. Repeat expand/prune until the desired horizon `k_max` is reached.

- **Inputs:** POMDP tuple, horizon `k_max` (finite-horizon case).
- **Outputs:** a pruned set of alpha vectors \(\Gamma\) (each tagged with its root action), representing the piecewise-linear value function and an implicit optimal policy over beliefs.
- **Stopping criterion:** fixed horizon `k_max`, since exact POMDP value iteration does not have a simple residual-based early stop analogous to MDP value iteration (though a residual test over a belief sample set is a common approximation, not part of the zero-order exact method here).
- **Computational constraint:** the number of possible \(h\)-step conditional plans grows as \(|\mathcal{A}|^{(|\mathcal{O}|^h-1)/(|\mathcal{O}|-1)}\)-like combinatorics; pruning is essential, but exact POMDP value iteration remains intractable beyond small state/observation spaces, motivating point-based and online belief-space methods (noted here only as the boundary case, not elaborated further per the zero-order scope of this cluster).

```
def alpha_dot(alpha, b_states, b):
    return sum(alpha[s] * b[s] for s in b_states)

def belief_lookahead_Q(pomdp, U_belief_fn, b, a):
    S, O = list(pomdp.S), list(pomdp.O)
    r = sum(pomdp.R(s, a) * b[s] for s in S)
    def p_o_given_b_a(o):
        total = 0.0
        for s in S:
            p_o_given_s_a = sum(pomdp.T(sp, s, a) * pomdp.O(o, a, sp) for sp in S)  # O(o | a, s'), argument order (o, a, s')
            total += b[s] * p_o_given_s_a
        return total
    acc = 0.0
    for o in O:
        p_o = p_o_given_b_a(o)
        if p_o == 0.0:
            continue
        b_next = belief_update(b, pomdp, a, o)
        acc += p_o * U_belief_fn(b_next)
    return r + pomdp.gamma * acc

def belief_greedy_action(pomdp, U_belief_fn, b):
    return max(pomdp.A, key=lambda a: belief_lookahead_Q(pomdp, U_belief_fn, b, a))
```

## 11. Zero-Order End-to-End Decision Loop

The following loop composes the mechanisms above into one process: build/solve a model, then act, observe, update belief (or state), and replan, matching the receding-horizon scheme used throughout.

```
def sequential_decision_loop(env, model, planner, is_pomdp, k_max_plan, rng, horizon):
    """
    env: simulator exposing .step(s_or_b, a) -> (s_next_or_obs, r, done)
    model: MDP or POMDP tuple-holding object (S, A, T, R, gamma[, O_space, O])
    planner: callable(model, current_belief_or_state) -> action
              (e.g., value_iteration-derived greedy policy, forward_search,
               or belief_lookahead_Q-based greedy_action)
    is_pomdp: whether to track a belief instead of the true state
    """
    s = env.reset()
    b = {s0: 1.0 / len(model.S) for s0 in model.S} if is_pomdp else None
    total_return = 0.0
    discount = 1.0

    for t in range(horizon):
        current = b if is_pomdp else s
        a = planner(model, current)                      # one decision step (Sections 3-10)
        s_next, signal, done = env.step(s, a)             # signal is (o, r) for POMDP, r for MDP

        if is_pomdp:
            o, r = signal
            b = belief_update(b, model, a, o)              # Section 9: belief update
        else:
            r = signal

        total_return += discount * r
        discount *= model.gamma
        s = s_next

        if done:
            break

    return total_return
```

- **Inputs:** a solved or online planner, an environment/simulator implementing the true (unknown to the belief-tracker, if POMDP) transition and observation dynamics, an initial state or diffuse initial belief, a horizon.
- **Outputs:** the realized discounted return, and implicitly the action/observation/belief trajectory.
- **Stopping criterion:** `done` flag from the environment or a fixed `horizon`.
- **Failure modes:** planner and belief tracker relying on a misspecified \(T\), \(R\), or \(O\) will produce actions optimal for the wrong model; belief updates degrade under model mismatch by becoming falsely overconfident, which is mitigated by using more diffuse transition/observation models rather than sharply peaked ones when the true dynamics are uncertain.

## 12. Validation Invariants

Use these as automatic checks on any implementation of the above mechanisms:

1. **Probability normalization.** For every distribution or belief vector \(p\): \(p(x) \ge 0\) for all \(x\), and \(\sum_x p(x) = 1\) within floating-point tolerance (e.g., \(10^{-8}\)).
2. **Bayes update consistency.** Applying `bayes_update` or `belief_update` and then summing the result must reproduce 1.0 (post-normalization), and the unnormalized evidence term must be nonnegative before normalization.
3. **Bellman residual monotonicity under value iteration.** For value iteration on a proper MDP (\(\gamma < 1\), bounded rewards), the sequence \(\lVert U_{k+1} - U_k\rVert_\infty\) must be non-increasing in the limit and shrink by a factor no worse than \(\gamma\) per sweep, since the backup is a \(\gamma\)-contraction; a residual that fails to shrink indicates a bug in the backup or an invalid (\(\gamma \ge 1\)) discount.
4. **Bellman equation fixed point.** After convergence, for every state \(s\), \(U(s)\) must equal \(\max_a Q(s,a)\) computed from the same \(T,R,\gamma\), and the greedy policy's one-step lookahead value must match \(U(s)\) to within the declared tolerance \(\delta\).
5. **Policy improvement monotonicity.** In policy iteration, \(U^{\pi_{k+1}}(s) \ge U^{\pi_k}(s)\) for all \(s\) at every iteration; a violation indicates an evaluation or improvement bug.
6. **Q-U-advantage consistency.** \(U(s) = \max_a Q(s,a)\) and \(A(s,a) = Q(s,a) - U(s) \le 0\), with equality exactly at the greedy action(s).
7. **Alpha-vector value bound.** For any belief \(b\) and any alpha vector \(\alpha \in \Gamma\) retained by pruning, \((\alpha)^\top b \le U^{*}(b)\) (the upper envelope property); the maximizing \(\alpha\) at a given \(b\) must be the one actually selected by the alpha-vector policy at that \(b\).
8. **Belief-state transition validity.** For the belief-state MDP transition function, \(\sum_{o} P(o \mid b, a) = 1\) for every \(b, a\); if this fails, the observation or transition model is inconsistent.
9. **Discount and return finiteness.** For \(\gamma \in [0,1)\) and bounded per-step reward \(\lvert r_t \rvert \le R_{\max}\), the discounted return must satisfy \(\bigl\lvert \sum_t \gamma^{t-1} r_t \bigr\rvert \le R_{\max}/(1-\gamma)\); any computed return exceeding this bound signals an implementation error (e.g., wrong discount application or reward scale).
10. **Online replanning statelessness.** In the end-to-end loop, the action selected at time \(t\) must be a function only of the current state or belief passed to `planner`, never of stored plan state from a previous call, consistent with the receding-horizon definition (re-planning from scratch at every step).
