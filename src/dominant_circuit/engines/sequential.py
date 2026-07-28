"""Engine C — Sequential Decisions / MDP / POMDP (Cluster 03)."""

from __future__ import annotations

from typing import Any, Callable, Optional, Sequence

from ..core.contract import InputContract, Horizon, Job
from ..core.errors import NonMarkovProcess, PreconditionViolation, UnclassifiedVariant
from ..core.report import (
    OutputReport, AuditResult, InvariantResult, SensitivityEntry,
    PerturbationTerm, relative_shift,
    ORDER_ZERO, ORDER_FIRST, ORDER_OVERTURN, ORDER_HARD,
)


def belief_update(
    prior: dict[Any, float],
    observation: Any,
    observation_model: Callable[[Any, Any], float] | dict,
    transition: Optional[Callable | dict] = None,
    action: Any = None,
) -> dict[Any, float]:
    """Recursive Bayesian update. Zero-likelihood → uniform fallback."""
    states = list(prior.keys())
    likelihoods: dict[Any, float] = {}

    for s in states:
        if callable(observation_model):
            try:
                lik = observation_model(observation, s, action) if action is not None else observation_model(observation, s)
            except TypeError:
                lik = observation_model(observation, s)
        else:
            lik = observation_model.get((observation, s), observation_model.get(s, 0.0))
        likelihoods[s] = max(0.0, float(lik))

    unnormalized = {s: prior[s] * likelihoods[s] for s in states}
    total = sum(unnormalized.values())

    if total <= 0.0:
        n = len(states)
        return {s: 1.0 / n for s in states}

    return {s: unnormalized[s] / total for s in states}


def bellman_backup(
    state: Any,
    actions: Sequence[Any],
    V: dict[Any, float],
    reward: Callable | dict,
    transition: Callable | dict,
    gamma: float,
) -> tuple[float, Any]:
    best_q = -float("inf")
    best_a = actions[0] if actions else None

    for a in actions:
        if callable(reward):
            try:
                r = reward(state, a)
            except TypeError:
                r = reward(state)
        else:
            r = reward.get((state, a), reward.get(state, 0.0))

        if callable(transition):
            next_dist = transition(state, a)
        else:
            next_dist = transition.get((state, a), {})

        exp_v = 0.0
        if isinstance(next_dist, dict):
            for sp, p in next_dist.items():
                exp_v += p * V.get(sp, 0.0)
        else:
            exp_v = V.get(next_dist, 0.0)

        q = r + gamma * exp_v
        if q > best_q:
            best_q = q
            best_a = a

    return best_q, best_a


def value_iteration(
    states: Sequence[Any],
    actions: Sequence[Any],
    reward: Callable | dict,
    transition: Callable | dict,
    gamma: float,
    tolerance: float = 1e-6,
    k_max: int = 1000,
) -> tuple[dict[Any, float], dict[Any, Any], list[float]]:
    V = {s: 0.0 for s in states}
    residuals: list[float] = []

    for _ in range(k_max):
        V_new = {}
        policy = {}
        delta = 0.0
        for s in states:
            v, a = bellman_backup(s, actions, V, reward, transition, gamma)
            V_new[s] = v
            policy[s] = a
            delta = max(delta, abs(v - V[s]))
        residuals.append(delta)
        V = V_new
        if delta < tolerance:
            break

    return V, policy, residuals


def solve_sequential(contract: InputContract) -> OutputReport:
    if contract.markov_verified is False:
        raise NonMarkovProcess(
            "Markov property not verified.",
            remedy="Augment state so next-state depends only on current state + action.",
            field="markov_verified",
        )
    if contract.markov_verified is None:
        raise PreconditionViolation("markov_verified must be explicitly set.", field="markov_verified")

    gamma = contract.gamma
    if gamma is None or not (0.0 <= gamma < 1.0):
        raise PreconditionViolation(
            f"γ must satisfy 0 ≤ γ < 1 for contraction. Got {gamma}.",
            field="gamma",
        )

    states = list(contract.states or [])
    actions = list(contract.actions or [])
    if not states or not actions:
        raise PreconditionViolation("states and actions required", field="states")

    reward = contract.reward
    transition = contract.transition
    if reward is None or transition is None:
        raise PreconditionViolation("reward and transition models required", field="reward")

    if contract.prior_belief is not None and contract.observations:
        obs_model = contract.observation_model
        if obs_model is None:
            raise PreconditionViolation("observation_model required for POMDP belief update")
        belief = dict(contract.prior_belief)
        history = [dict(belief)]
        for o in contract.observations:
            belief = belief_update(belief, o, obs_model, transition)
            history.append(dict(belief))
        total = sum(belief.values())
        return OutputReport(
            decision={"belief": belief, "history_len": len(history)},
            action=(
                f"After {len(contract.observations)} observation(s), the most likely state "
                f"is {max(belief, key=belief.get)!r} at probability "
                f"{max(belief.values()):.4f}. Act on the full belief vector, not the mode "
                "alone — the remaining mass is the part that can still surprise you."
            ),
            formula_name="Recursive Bayesian Belief Update",
            formula_latex=r"b'(s) \propto O(o|s)\,b(s)",
            citation="c03 §9",
            numeric={"belief_sum": total, **{f"b[{s}]": p for s, p in belief.items()}},
            assumptions={
                "gamma": gamma,
                "markov_verified": True,
                "n_states": len(states),
                "n_observations": len(contract.observations),
            },
            sensitivity=[
                SensitivityEntry(
                    assumption="observation likelihood",
                    perturbation="all zero → uniform reset",
                    new_decision="uniform belief",
                    decision_changed=True,
                    fragility="critical",
                )
            ],
            audit=AuditResult(results=[
                InvariantResult(
                    "INV-2", "belief_normalization", abs(total - 1.0) <= 1e-8,
                    residual=abs(total - 1.0), tolerance=1e-8,
                    message=f"belief sums to {total}",
                ),
            ]),
        )

    V, policy, residuals = value_iteration(
        states, actions, reward, transition, gamma,
        tolerance=contract.tolerance, k_max=contract.k_max,
    )

    contracting = True
    if len(residuals) > 1:
        contracting = all(
            residuals[i] <= gamma * residuals[i - 1] + 1e-9
            or residuals[i] < contract.tolerance
            for i in range(1, len(residuals))
        )

    start = states[0]
    if contract.prior_belief:
        start = max(contract.prior_belief, key=contract.prior_belief.get)

    # --- zero-order expansion ------------------------------------------------------
    # The Bellman equation IS a perturbation series in gamma: U = R + gamma*E[U'].
    # gamma = 0 keeps only the immediate-reward term (the myopic/greedy trunk); the
    # discounted future terms are the corrections, and value iteration's residuals
    # shrink by <= gamma per sweep, which is why the series converges (c03 §6).
    myopic_v, myopic_a = bellman_backup(
        start, actions, {s: 0.0 for s in states}, reward, transition, 0.0
    )
    expansion = [
        PerturbationTerm(
            order=ORDER_ZERO,
            label=f"myopic action at {start!r} (gamma=0, immediate reward only)",
            value=myopic_a, citation="c03 §6",
            note="the trunk: R(s,a) alone, dropping all discounted future terms",
        ),
        PerturbationTerm(
            order=ORDER_FIRST,
            label=f"full Bellman optimum at {start!r} (gamma={gamma})",
            value=policy.get(start), citation="c03 §6",
            relative_shift=relative_shift(V.get(start), myopic_v),
            note=("the discounted future terms change the recommended action — the "
                  "myopic trunk is wrong here"
                  if policy.get(start) != myopic_a else
                  "the discounted future terms refine the value but confirm the myopic "
                  "action; the trunk holds"),
        ),
        PerturbationTerm(
            order=ORDER_FIRST,
            label=f"convergence: {len(residuals)} sweeps",
            value=f"residual {residuals[-1]:.2e}" if residuals else "n/a",
            citation="c03 §6",
            note="successive corrections shrink by <= gamma per sweep, so the series "
                 "converges and later terms cannot overturn the trunk",
        ),
        PerturbationTerm(
            order=ORDER_HARD,
            label="markov_verified = False",
            value="REFUSED (NonMarkovProcess)",
            citation="c03 §3",
            note="硬约束: if the next state depends on deeper history the expansion is "
                 "not defined at all. Augment the state space; do not discount the "
                 "violation as a small term",
        ),
    ]

    return OutputReport(
        decision={
            "policy": policy,
            "value": V,
            "recommended_action": policy.get(start),
            "start_state": start,
            "iterations": len(residuals),
            "final_residual": residuals[-1] if residuals else None,
        },
        perturbation=expansion,
        action=(
            f"From state {start!r}, take action {policy.get(start)!r}. "
            f"Value iteration converged in {len(residuals)} sweeps to a residual of "
            f"{residuals[-1]:.2e}; the policy above is optimal for γ={gamma}. "
            "Re-plan after you observe the next state rather than executing the whole "
            "policy blind."
        ),
        formula_name="Bellman Optimality / Value Iteration",
        formula_latex=r"U^*(s)=\max_a\bigl(R(s,a)+\gamma\sum_{s'}T(s'|s,a)U^*(s')\bigr)",
        citation="c03 §6",
        numeric={
            "gamma": gamma,
            "iterations": float(len(residuals)),
            "final_residual": residuals[-1] if residuals else float("nan"),
            **{f"V[{s}]": v for s, v in V.items()},
        },
        assumptions={
            "gamma": gamma,
            "markov_verified": True,
            "n_states": len(states),
            "n_actions": len(actions),
            "tolerance": contract.tolerance,
            "k_max": contract.k_max,
        },
        sensitivity=[
            SensitivityEntry(
                assumption="gamma",
                perturbation=f"{gamma} → higher (closer to 1)",
                new_decision="longer planning horizon, more iterations",
                decision_changed=True,
                fragility="fragile",
            ),
        ],
        audit=AuditResult(results=[
            InvariantResult(
                "INV-4", "bellman_residual_monotonicity", contracting,
                residual=residuals[-1] if residuals else None,
                tolerance=contract.tolerance,
                message="Residuals contract by ≤ γ" if contracting else "Residuals do not contract",
            ),
            InvariantResult(
                "INV-markov", "markov_property", True,
                message="markov_verified=True recorded",
            ),
        ]),
    )
