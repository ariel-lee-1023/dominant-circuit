"""Stage 1 — Completeness checking and weight screening. No I/O; the host asks.

Two distinct jobs live here:

  * **Completeness** — `missing_fields` / `next_question`: what must be known before
    anything can be computed at all.
  * **Weight** — `overturn_test` / `elicitation_plan`: of the things that *could*
    be known, which are worth asking about.

Screening records bounded action comparisons. Untested factors remain unresolved;
a finite probe set never justifies automatically discarding a factor.
"""

from __future__ import annotations

from dataclasses import dataclass, replace, fields
from typing import Any, Optional, Sequence

from .contract import InputContract, Job, Horizon, Information, Payoff
from .errors import ContractIncomplete, DominantCircuitError

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
    "markov_verified": "What evidence and scope support treating the next state as depending only on the current state and action?",
    "independence_assumptions": "Has mutual (or pairwise) utility/preferential independence been verified, and against which attribute subsets?",
    "attributes": "What are the attributes and their explicit [worst, best] ranges?",
    "scaling_constants": "What are the scaling constants k_i, each attached to its assessed range?",
    "risk_attitude": "Is the decision maker risk-averse, risk-neutral, or risk-prone?",
    "flip_test_preferred_pairing": "In the two 50-50 gambles built from the same outcomes, do you prefer the 'straight' pairing, the 'crossed' pairing, or are you indifferent?",
}


# --- Weight: the overturn test ----------------------------------------------------
#
# Weight is the magnitude of causal control a factor exerts over the outcome, GIVEN
# a concrete goal, a time scale, and defined objects of comparison. There is no
# standard answer; it depends entirely on the objective function. So weight is not a
# property the library can compute from a factor in isolation — it is a property of
# a factor *relative to a stated goal*, and the goal is the user's to state.
#
# These three are therefore not screenable. Without them the objective function does
# not exist, so no factor has a weight yet and the overturn test has nothing to test
# against. Everything else is screenable.
WEIGHT_PREREQUISITES: dict[str, tuple[str, ...]] = {
    "goal": ("payoff", "attributes", "scaling_constants", "risk_attitude"),
    "time_scale": ("horizon", "gamma", "n", "n_max", "stop_prob_per_step"),
    "comparison_set": ("alternatives", "states", "actions"),
}

# Fields that are structural preconditions rather than weighted factors: without
# them the problem is not merely imprecise, it is undefined or uncomputable.
_UNSCREENABLE = frozenset(
    {"job", "payoff_diverges", "markov_verified", "independence_assumptions"}
    | {f for group in WEIGHT_PREREQUISITES.values() for f in group}
)

# One concrete alternative world per screenable factor. Each probe is a full override
# dict, not a bare value, because some factors only mean anything in pairs (recall
# without its acceptance probability is not a state of the world). Probe values are
# corpus-calibrated — 0.5 is the only recall/rejection probability c01 calibrates.
_OVERTURN_PROBES: dict[str, list[dict[str, Any]]] = {
    "recall_allowed": [{"recall_allowed": True, "recall_accept_prob": 0.5}],
    "rejection_prob": [{"rejection_prob": 0.5}],
    "recall_accept_prob": [{"recall_allowed": True, "recall_accept_prob": 0.5}],
    "exact_finite_n": [{"exact_finite_n": False}],
    "search_cost": [{"search_cost": 0.02}, {"search_cost": 0.25}],
    "flip_test_preferred_pairing": [
        {"flip_test_performed": True, "flip_test_preferred_pairing": None},
        {"flip_test_performed": True, "flip_test_preferred_pairing": "straight"},
    ],
    "tolerance": [{"tolerance": 1e-3}],
    "k_max": [{"k_max": 10}],
}

_REFUSED = object()


@dataclass
class OverturnResult:
    field: str
    overturns: bool
    baseline_decision: Any
    outcomes: list
    verdict: str
    outcome: str = "untested"
    probes: list = None
    comparison_scope: str = "engine_action"
    schema_version: int = 2

    @property
    def is_small_quantity(self) -> bool:
        """Deprecated: finite probes never prove a factor irrelevant."""
        return False


def decision_projection(report, job):
    d = report.decision
    if job == Job.MULTIOBJECTIVE:
        return sorted(d.get("tie_set", [d.get("best_alternative")]))
    if job == Job.SEQUENTIAL:
        return d.get("policy") if "policy" in d else None
    if isinstance(d, dict):
        return {k:v for k,v in d.items() if k not in {"n", "history_len"}}
    return d


def model_projection(report, job):
    if job == Job.MULTIOBJECTIVE:
        return report.decision.get('form')
    keys = ('horizon','information','payoff','recall_allowed','recall_accept_prob','rejection_prob') if job == Job.STOPPING else ('gamma','n_states','n_actions')
    return {k:report.assumptions.get(k) for k in keys}


def overturn_test(contract, field, probes=None) -> OverturnResult:
    from .dispatch import dispatch
    from .errors import UnclassifiedVariant, PreconditionViolation
    from .evidence import scenario_branch
    valid_fields = {f.name for f in fields(contract)}
    if field not in valid_fields:
        raise ValueError(f"Unknown contract field: {field}")
    require_complete(contract)
    baseline = dispatch(contract.job, replace(contract))
    trials = list(probes) if probes is not None else _OVERTURN_PROBES.get(field, [])
    outcomes, records = [], []
    for probe in trials:
        if not set(probe) <= valid_fields:
            raise ValueError("Probe contains unknown contract field")
        try:
            result = dispatch(contract.job, scenario_branch(contract, probe, "screening"))
            before = decision_projection(baseline, contract.job)
            after = decision_projection(result, contract.job)
            record = dict(execution_status="completed",
                model_changed=model_projection(result, contract.job) != model_projection(baseline, contract.job),
                action_changed=None if before is None or after is None else before != after,
                feasibility_changed=result.decision.get("feasibility") != baseline.decision.get("feasibility")
                    if isinstance(result.decision, dict) and isinstance(baseline.decision, dict) else None)
            outcomes.append((probe, result.decision))
        except DominantCircuitError as exc:
            status = "unsupported" if isinstance(exc, UnclassifiedVariant) else "invalid" if isinstance(exc, (PreconditionViolation, ContractIncomplete)) else "failed"
            record = dict(execution_status=status, model_changed=None, action_changed=None,
                          feasibility_changed=None, limitation=str(exc))
            outcomes.append((probe, "REFUSED"))
        except (ValueError, TypeError, ArithmeticError, RuntimeError) as exc:
            record = dict(execution_status='invalid' if isinstance(exc,(ValueError,TypeError)) else 'failed',
                model_changed=None,action_changed=None,feasibility_changed=None,limitation=str(exc))
            outcomes.append((probe,'REFUSED'))
        records.append(dict(perturbation=probe, baseline_revision=contract.revision,
            origin='model_proposal',acceptance='scenario_only',method='explicit_redispatch',
            dependencies=[v.input_id for v in contract.provenance.values() if hasattr(v,'input_id')], **record))
    changed = any(r["action_changed"] is True or r["feasibility_changed"] is True for r in records)
    completed = records and all(r["execution_status"] == "completed" and r["action_changed"] is not None for r in records)
    outcome = "changes_decision" if changed else "stable_within_tested_bounds" if completed else "untested"
    return OverturnResult(field, changed, baseline.decision, outcomes,
        f"{field}: {outcome}. Coverage is limited to the listed probes; no discard instruction follows.",
        outcome, records, "full_policy" if contract.job == Job.SEQUENTIAL else "engine_action")


def screenable_fields(contract: InputContract) -> list[str]:
    """Factors whose weight can be tested. Excludes the prerequisites of weight
    itself, which must be stated before any factor has a weight at all."""
    job = contract.job
    candidates = set(_OVERTURN_PROBES)
    if job == Job.STOPPING:
        candidates &= {"recall_allowed", "recall_accept_prob", "rejection_prob",
                       "exact_finite_n", "search_cost"}
    elif job == Job.MULTIOBJECTIVE:
        candidates &= {"flip_test_preferred_pairing"}
    elif job == Job.SEQUENTIAL:
        candidates &= {"tolerance", "k_max"}
    return sorted(candidates - _UNSCREENABLE)


def elicitation_plan(contract: InputContract) -> dict[str, Any]:
    """Return prerequisites and screening coverage, without a universal stopping rule.

    Completed action-changing probes are load-bearing. Completed unchanged probes
    are stable only within their tested bounds. Other coverage remains untested.
    The deprecated droppable list is always empty.
    """
    required = missing_fields(contract)
    if required:
        return {
            "required": required,
            "load_bearing": [],
            "droppable": [],
            "note": ("Weight is undefined until the goal, time scale and comparison "
                     "set are stated. Ask the required fields first; screening "
                     "cannot begin without a conclusion to test against."),
        }

    results = {name: overturn_test(contract, name) for name in screenable_fields(contract)}
    return {
        "required": [],
        "load_bearing": [name for name,r in results.items() if r.outcome == "changes_decision"],
        "stable_within_tested_bounds": [name for name,r in results.items() if r.outcome == "stable_within_tested_bounds"],
        "untested": [name for name,r in results.items() if r.outcome == "untested"],
        "droppable": [],
        "coverage": results,
        "note": "Finite screening does not establish irrelevance outside tested bounds.",
    }


def classify_job(contract: InputContract) -> Job:
    """SPEC §5. Determine the job from CONTRACT FIELDS ONLY.

    Never from substring matching on user prose — that was defect D-06, and it
    is what this rewrite exists to eliminate. A phrase like "what are my options"
    does not tell you whether the user faces a stream to stop, a fixed set to
    rank, or a policy to plan; only the structure they described does.

    Raises ContractIncomplete(field='job') when the fields do not determine it.
    """
    if contract.job is not None:
        return contract.job

    # Sequential: a state/action space, or dynamics, or a belief to track.
    sequential_signals = (
        contract.states is not None or contract.actions is not None
        or contract.transition is not None or contract.observation_model is not None
        or contract.prior_belief is not None or contract.markov_verified is not None
        or contract.gamma is not None
    )
    # Multiobjective: several attributes traded off against each other.
    multiobjective_signals = (
        contract.attributes is not None or contract.scaling_constants is not None
        or contract.independence_assumptions is not None
    )
    # Stopping: a search over a horizon with recall/rejection/search-cost structure.
    stopping_signals = (
        contract.horizon is not None or contract.n is not None
        or contract.n_max is not None or contract.stop_prob_per_step is not None
        or contract.recall_allowed is not None or contract.rejection_prob is not None
        or contract.search_cost is not None or contract.payoff_diverges is not None
    )

    matched = [
        job for job, signal in (
            (Job.SEQUENTIAL, sequential_signals),
            (Job.MULTIOBJECTIVE, multiobjective_signals),
            (Job.STOPPING, stopping_signals),
        )
        if signal
    ]

    if len(matched) == 1:
        return matched[0]

    if not matched:
        raise ContractIncomplete(
            "No contract field determines the job. Nothing has been elicited that "
            "distinguishes a stopping problem from a multi-objective ranking or a "
            "sequential plan.",
            remedy=QUESTION_BANK["job"],
            field="job",
        )

    raise ContractIncomplete(
        "The elicited fields are consistent with more than one job "
        f"({', '.join(j.value for j in matched)}); the job cannot be inferred "
        "from structure alone.",
        remedy=QUESTION_BANK["job"],
        field="job",
    )


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
        if contract.payoff in (Payoff.BEST_OR_NOTHING, Payoff.DURATION):
            if contract.recall_allowed is None:
                missing.append("recall_allowed")
            if contract.rejection_prob is None:
                missing.append("rejection_prob")
        if contract.payoff == Payoff.COST_OF_SEARCH:
            if contract.recall_allowed is None:
                missing.append("recall_allowed")
            if contract.information is None:
                missing.append("information")
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
        if contract.prior_belief is not None:
            return [name for name in ('observation_model','observations') if getattr(contract,name) is None]
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
