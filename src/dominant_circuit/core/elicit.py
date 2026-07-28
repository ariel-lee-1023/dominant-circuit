"""Stage 1 — Completeness checking. No I/O. Host AI asks the questions."""

from __future__ import annotations

from typing import Optional

from .contract import InputContract, Job, Horizon, Information, Payoff
from .errors import ContractIncomplete

QUESTION_BANK = {
    "job": "Is this a stopping problem, a multi-objective ranking, or a sequential plan?",
    "horizon": "Is the total number of options/time fixed and known, fixed but unknown, open-ended/stochastic, or unbounded?",
    "n": "What is the exact pool size n?",
    "n_max": "What is the upper bound n_max on the unknown pool size?",
    "stop_prob_per_step": "What is the per-step probability that the opportunity stream ends?",
    "information": "Can you only compare options relatively (ordinal) or do you have absolute scores (cardinal)?",
    "recall_allowed": "Once you pass on an option, can you revisit it later?",
    "recall_accept_prob": "If you recall a past option, what is the probability it is still available?",
    "rejection_prob": "What is the probability that an accepted offer is declined by the candidate?",
    "payoff_diverges": "Does the expected reward grow without bound if you never stop (e.g. triple-or-nothing)?",
    "payoff": "What is the payoff structure: best-or-nothing, net-value-minus-cost, ruin-risk, multiattribute, or discounted return?",
    "search_cost": "What is the per-look cost, normalized to the [0,1] outcome scale?",
    "ruin_success_prob": "What is the per-trial probability q that a trial succeeds rather than wiping out everything accumulated?",
    "ruin_mean_gain": "What is the average gain m per successful trial?",
    "gamma": "What discount factor γ ∈ [0,1) should be used?",
    "markov_verified": "Have you confirmed that the next state depends only on the current state and action (Markov property)?",
    "independence_assumptions": "Has mutual (or pairwise) utility/preferential independence been verified, and against which attribute subsets?",
    "attributes": "What are the attributes and their explicit [worst, best] ranges?",
    "scaling_constants": "What are the scaling constants k_i, each attached to its assessed range?",
    "risk_attitude": "Is the decision maker risk-averse, risk-neutral, or risk-prone?",
}


def missing_fields(contract: InputContract) -> list[str]:
    missing: list[str] = []
    if contract.job is None:
        return ["job"]

    if contract.job == Job.STOPPING:
        if contract.horizon is None:
            missing.append("horizon")
        if contract.payoff is None:
            missing.append("payoff")
        if contract.payoff_diverges is None:
            missing.append("payoff_diverges")
        if contract.information is None and contract.payoff == Payoff.BEST_OR_NOTHING:
            missing.append("information")
        if contract.horizon == Horizon.FIXED_KNOWN and contract.n is None:
            missing.append("n")
        if contract.horizon == Horizon.FIXED_UNKNOWN_UNIFORM and contract.n_max is None:
            missing.append("n_max")
        if contract.horizon == Horizon.OPEN_ENDED_STOCHASTIC and contract.stop_prob_per_step is None:
            missing.append("stop_prob_per_step")
        if contract.payoff == Payoff.COST_OF_SEARCH and contract.search_cost is None:
            missing.append("search_cost")
        if contract.payoff == Payoff.RUIN_RISK:
            # Burglar Rule, c01 §11: ceiling = m*q/(1-q). Both are required.
            if contract.ruin_success_prob is None:
                missing.append("ruin_success_prob")
            if contract.ruin_mean_gain is None:
                missing.append("ruin_mean_gain")
        if contract.recall_allowed is True and contract.recall_accept_prob is None:
            missing.append("recall_accept_prob")

    elif contract.job == Job.MULTIOBJECTIVE:
        # `is None` means "never elicited" -> Stage 1 asks for it.
        # An empty collection is elicited data ("asked, nothing recorded") and must
        # fall through to Stage 2, where IndependenceNotVerified is the right answer.
        if contract.attributes is None:
            missing.append("attributes")
        if contract.independence_assumptions is None:
            missing.append("independence_assumptions")
        if contract.scaling_constants is None:
            missing.append("scaling_constants")

    elif contract.job == Job.SEQUENTIAL:
        if contract.horizon is None:
            missing.append("horizon")
        if contract.gamma is None:
            missing.append("gamma")
        if contract.markov_verified is None:
            missing.append("markov_verified")
        if contract.states is None:
            missing.append("states")
        if contract.actions is None:
            missing.append("actions")

    return missing


def next_question(contract: InputContract) -> Optional[str]:
    miss = missing_fields(contract)
    if not miss:
        return None
    field = miss[0]
    return QUESTION_BANK.get(field, f"Please supply the value for '{field}'.")


def require_complete(contract: InputContract) -> None:
    miss = missing_fields(contract)
    if miss:
        field = miss[0]
        raise ContractIncomplete(
            f"Input Contract incomplete. Missing: {miss}",
            remedy=QUESTION_BANK.get(field, f"Elicit '{field}'."),
            field=field,
        )
