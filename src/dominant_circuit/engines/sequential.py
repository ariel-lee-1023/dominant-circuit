"""Engine C — Sequential Decisions / MDP / POMDP (Cluster 03)."""

from __future__ import annotations

from typing import Any, Callable, Optional, Sequence
from dataclasses import dataclass
import math

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
    """Static-state Bayesian conditioning. Impossible evidence has no posterior.

    Dynamic filtering is explicitly unsupported here: callers must not confuse
    static conditioning with POMDP action planning or ignored transition data.
    """
    if transition is not None:
        raise UnclassifiedVariant("Dynamic belief prediction is not implemented", field="transition",
            remedy="Provide a separately computed predictive prior and condition on the observation.")
    if not prior or any(not isinstance(p,(int,float)) or not math.isfinite(p) or p < 0 for p in prior.values()) or not math.isclose(sum(prior.values()),1.,abs_tol=1e-12,rel_tol=0):
        raise PreconditionViolation("Prior must be finite, nonnegative and normalized",field="prior_belief")
    likelihoods = {}
    for state in prior:
        try:
            if callable(observation_model):
                lik = observation_model(observation,state,action) if action is not None else observation_model(observation,state)
            else:
                lik = observation_model[observation,state] if (observation,state) in observation_model else observation_model[state]
        except (KeyError,TypeError) as exc:
            raise PreconditionViolation("Missing observation likelihood",field="observation_model") from exc
        if not isinstance(lik,(int,float)) or not math.isfinite(lik) or lik < 0 or lik > 1:
            raise PreconditionViolation("Likelihoods must be probabilities in [0,1]",field="observation_model")
        likelihoods[state] = prior[state]*lik
    total = sum(likelihoods.values())
    if total <= 0:
        raise PreconditionViolation("Observation has zero probability under the model; posterior undefined",
            field="observation_model",remedy="Check the observation, prior or likelihood model; do not invent a uniform posterior.")
    return {state:p/total for state,p in likelihoods.items()}


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


@dataclass
class ValueIterationResult:
    values: dict
    policy: dict
    iterate_differences: list[float]
    termination_reason: str
    bellman_residual: float
    value_error_bound: float
    tolerance: float
    method: str = "synchronous_value_iteration"
    criterion: str = "returned_value_bellman_residual"

    def __iter__(self):
        # Compatibility: the third legacy tuple element is iterate differences.
        yield self.values
        yield self.policy
        yield self.iterate_differences


def validated_mdp(states, actions, reward, transition, terminal_states=()):
    if not states or not actions or len(set(states)) != len(states) or len(set(actions)) != len(actions):
        raise PreconditionViolation("Nonempty unique states and actions required", field="states")
    terminals = set(terminal_states)
    if not terminals <= set(states):
        raise PreconditionViolation("Unknown terminal state", field="terminal_states")
    rewards, transitions = {}, {}
    for state in states:
        for action in actions:
            if state in terminals:
                if callable(reward) or callable(transition):
                    raise PreconditionViolation("Explicit terminals require table models",field="terminal_states")
                supplied_reward = reward.get((state,action),reward.get(state,0.))
                supplied_transition = transition.get((state,action),{state:1.})
                if supplied_reward != 0. or supplied_transition != {state:1.}:
                    raise PreconditionViolation("Terminal data contradicts zero absorbing semantics",field="terminal_states")
                rewards[state, action], transitions[state, action] = 0., {state: 1.}
                continue
            try:
                if callable(reward):
                    r = reward(state, action)
                else:
                    r = reward[state, action] if (state, action) in reward else reward[state]
                dist = transition(state, action) if callable(transition) else transition[state, action]
            except (KeyError, TypeError) as exc:
                raise PreconditionViolation("Missing reward or transition row", field="transition") from exc
            if not isinstance(r, (int, float)) or not math.isfinite(r):
                raise PreconditionViolation("Finite rewards required", field="reward")
            if not isinstance(dist, dict) or not dist or not set(dist) <= set(states):
                raise PreconditionViolation("Transition must name known successor states", field="transition")
            if any(not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in dist.values()) or not math.isclose(sum(dist.values()), 1., abs_tol=1e-12, rel_tol=0):
                raise PreconditionViolation("Transition probabilities must be finite, nonnegative and sum to one", field="transition")
            rewards[state, action], transitions[state, action] = r, dict(dist)
    return rewards, transitions


def value_iteration(states, actions, reward, transition, gamma, tolerance=1e-6,
                    k_max=1000, terminal_states=()) -> ValueIterationResult:
    """Tolerance is a returned-value Bellman residual tolerance (schema 2).

    For this finite bounded discounted MDP, residual/(1-gamma) bounds value
    error. Invalid inputs raise before iteration; overflow returns diagnostics.
    """
    if isinstance(k_max, bool) or not isinstance(k_max, int) or k_max <= 0:
        raise PreconditionViolation("k_max must be a positive integer", field="k_max")
    if not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or tolerance <= 0:
        raise PreconditionViolation("tolerance must be finite and positive", field="tolerance")
    if not isinstance(gamma, (int, float)) or not math.isfinite(gamma) or not 0 <= gamma < 1:
        raise PreconditionViolation("gamma must satisfy 0 <= gamma < 1", field="gamma")
    reward, transition = validated_mdp(states, actions, reward, transition, terminal_states)
    values = {s: 0. for s in states}
    differences = []
    reason = "budget_exhausted"
    for _ in range(k_max):
        updated = {s: bellman_backup(s, actions, values, reward, transition, gamma)[0] for s in states}
        if not all(math.isfinite(v) for v in updated.values()):
            reason = "numerical_failure"
            break
        differences.append(max(abs(updated[s] - values[s]) for s in states))
        values = updated
        backups = {s: bellman_backup(s, actions, values, reward, transition, gamma) for s in states}
        residual = max(abs(backups[s][0] - values[s]) for s in states)
        if not math.isfinite(residual):
            reason = "numerical_failure"
            break
        if residual <= tolerance:
            reason = "converged"
            break
    backups = {s: bellman_backup(s, actions, values, reward, transition, gamma) for s in states}
    residual = max(abs(backups[s][0] - values[s]) for s in states)
    return ValueIterationResult(values, {s: (None if s in terminal_states else backups[s][1]) for s in states},
        differences, reason, residual, residual / (1-gamma), tolerance)


def solve_sequential(contract: InputContract) -> OutputReport:
    if contract.prior_belief is not None:
        if contract.observations is None or contract.observation_model is None:
            raise PreconditionViolation("Observations and likelihood model required",field="observations")
        if contract.transition is not None or contract.reward is not None:
            raise UnclassifiedVariant("Belief estimation does not compose with dynamic action planning",field="transition")
        belief = dict(contract.prior_belief)
        for observation in contract.observations:
            belief = belief_update(belief,observation,contract.observation_model)
        if not contract.observations:
            belief = belief_update(belief,None,{s:1. for s in belief})
        return OutputReport(decision={"belief":belief,"history_len":len(contract.observations)+1},
            formula_name="Static Bayesian Belief Update",formula_latex=r"b'(s) \propto O(o|s)b(s)",
            citation="c03 §9", numeric={"belief_sum":sum(belief.values())},
            assumptions={"model":"static hidden state; supplied likelihoods"}, sensitivity=[],
            audit=AuditResult([InvariantResult("INV-2","belief_normalization",True,
                message="Finite nonnegative normalized posterior")]),
            action="Computed posterior belief; no action plan was computed.")
    if contract.horizon != Horizon.INFINITE_DISCOUNTED:
        raise UnclassifiedVariant("Only infinite-discounted MDP semantics are implemented", field="horizon", remedy="Supply a supported horizon or a finite-horizon solver.")
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

    reward, transition = validated_mdp(states, actions, reward, transition, contract.terminal_states)
    computation = value_iteration(
        states, actions, reward, transition, gamma,
        tolerance=contract.tolerance, k_max=contract.k_max, terminal_states=contract.terminal_states,
    )

    V, policy, residuals = computation
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
            label=f"returned Bellman greedy action at {start!r} (gamma={gamma})",
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
            label=f"{computation.termination_reason}: {len(residuals)} sweeps",
            value=f"Bellman residual {computation.bellman_residual:.2e}",
            citation="c03 §6",
            note="Contraction is diagnostic; completion uses the returned-value residual. Future terms can change the action.",
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
            "final_residual": computation.bellman_residual,
            "last_iterate_difference": residuals[-1] if residuals else None,
            "termination_reason": computation.termination_reason,
            "value_error_bound": computation.value_error_bound,
            "criterion": computation.criterion,
            "method": computation.method,
        },
        perturbation=expansion,
        action=(f"Computed greedy action at {start!r}: {policy.get(start)!r}. "
                f"Termination: {computation.termination_reason}; returned-value Bellman residual "
                f"{computation.bellman_residual:.3g}; value error bound "
                f"{computation.value_error_bound:.3g} under a finite bounded discounted MDP."),
        formula_name="Bellman Optimality / Value Iteration",
        formula_latex=r"U^*(s)=\max_a\bigl(R(s,a)+\gamma\sum_{s'}T(s'|s,a)U^*(s')\bigr)",
        citation="c03 §6",
        numeric={
            "gamma": gamma,
            "iterations": float(len(residuals)),
            "final_residual": computation.bellman_residual,
            "value_error_bound": computation.value_error_bound,
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
