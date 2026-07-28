"""Stage 1 — Completeness checking and weight screening. No I/O; the host asks.

Two distinct jobs live here:

  * **Completeness** — `missing_fields` / `next_question`: what must be known before
    anything can be computed at all.
  * **Weight** — `overturn_test` / `elicitation_plan`: of the things that *could*
    be known, which are worth asking about.

The second exists because 细节是无穷的 — details are infinite. Asking "what else
haven't I considered?" never terminates. The only terminating question is the
overturn test: *is the presence or absence of this factor sufficient to overturn my
current conclusion?* If not, it is a high-order small quantity and belongs outside
the dominant equation.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
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
    "markov_verified": "Have you confirmed that the next state depends only on the current state and action (Markov property)?",
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
    """The answer to the only question that terminates: could this factor flip it?"""
    field: str
    overturns: bool
    baseline_decision: Any
    outcomes: list[tuple[dict[str, Any], Any]]
    verdict: str

    @property
    def is_small_quantity(self) -> bool:
        """True when the factor cannot overturn the conclusion — a high-order term.
        Throw it out of the dominant equation; do not spend elicitation on it."""
        return not self.overturns


def overturn_test(
    contract: InputContract,
    field: str,
    probes: Optional[Sequence[dict[str, Any]]] = None,
) -> OverturnResult:
    """翻盘检验. Is the presence or absence of this factor sufficient to overturn the
    conclusion the contract currently yields?

    Not "what have I not considered" — that never terminates. This asks the single
    terminating question, and answers it by actually recomputing.

    A refusal counts as an overturn: if setting the factor makes the problem
    uncomputable or uncalibrated, the factor is emphatically load-bearing.

    Requires a contract that already yields a conclusion; raises `ContractIncomplete`
    otherwise, because a factor has no weight until there is a goal to weigh it against.
    """
    from .dispatch import dispatch          # deferred: dispatch imports engines

    job = contract.job
    if job is None:
        raise ContractIncomplete(
            "The overturn test needs a conclusion to test against, and that needs a job.",
            remedy=QUESTION_BANK["job"], field="job",
        )
    still_missing = missing_fields(contract)
    if still_missing:
        raise ContractIncomplete(
            "The overturn test needs a current conclusion to test against; the "
            f"contract is still missing {still_missing}. Weight is undefined until "
            "the goal, time scale and comparison set are stated.",
            remedy=QUESTION_BANK.get(still_missing[0], f"Elicit '{still_missing[0]}'."),
            field=still_missing[0],
        )

    baseline = dispatch(job, replace(contract)).decision

    trials = list(probes) if probes is not None else _OVERTURN_PROBES.get(field, [])
    if not trials:
        return OverturnResult(
            field=field, overturns=False, baseline_decision=baseline, outcomes=[],
            verdict=(f"No probe defined for {field!r}; no overturn demonstrated. "
                     "Supply `probes` to test it explicitly rather than assuming."),
        )

    outcomes: list[tuple[dict[str, Any], Any]] = []
    overturns = False
    for probe in trials:
        try:
            result = dispatch(job, replace(contract, **probe)).decision
        except DominantCircuitError:
            result = _REFUSED
        outcomes.append((probe, "REFUSED" if result is _REFUSED else result))
        if result is _REFUSED or result != baseline:
            overturns = True

    if overturns:
        verdict = (
            f"{field!r} has overturn capacity: at least one calibrated alternative "
            "changes the conclusion (or voids it). It is load-bearing — elicit it "
            "properly and state it in the assumptions."
        )
    else:
        verdict = (
            f"{field!r} cannot overturn the conclusion under the probes tested, so it "
            "is a high-order small quantity for THIS goal. Throw it out of the "
            "dominant equation; do not spend the user's attention on it."
        )
    return OverturnResult(field, overturns, baseline, outcomes, verdict)


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
    """What to ask next, and what to stop asking about.

    Returns three lists:
      `required`     — must be answered before anything computes. Not screenable:
                       these ARE the goal, time scale and comparison set, and weight
                       is undefined without them.
      `load_bearing` — passed the overturn test. Worth the user's attention.
      `droppable`    — failed it. High-order small quantities for this goal; the
                       host should NOT ask about these.

    Once `required` is empty, the plan is the honest answer to "am I done asking?"
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

    load_bearing: list[str] = []
    droppable: list[str] = []
    for field_name in screenable_fields(contract):
        if overturn_test(contract, field_name).overturns:
            load_bearing.append(field_name)
        else:
            droppable.append(field_name)

    return {
        "required": [],
        "load_bearing": load_bearing,
        "droppable": droppable,
        "note": ("Contract complete. Ask only about `load_bearing`; `droppable` "
                 "factors cannot change the conclusion for this goal."),
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
