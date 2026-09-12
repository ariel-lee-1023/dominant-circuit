"""Versioned host evidence, translation and revision records. Pure data, no I/O.

Evidence references identify records held by the authorized host. Adoption records
intended use, never empirical truth. Export retains references, not conversations.
"""

from __future__ import annotations
from dataclasses import dataclass, field, fields, is_dataclass
from copy import deepcopy
from enum import Enum
import math
from typing import Any
from .contract import InputContract, Job
from .errors import PreconditionViolation
from .dependencies import dependency_closure

SCHEMA_VERSION = 2


@dataclass
class ConsequentialInput:
    input_id: str
    value: Any = None
    origin: str = "legacy"
    evidence_ref: str | None = None
    acceptance: str = "unresolved"
    scope: str = ""
    revision: int = 1
    uncertainty: Any = None
    dependencies: list[str] = field(default_factory=list)
    adoption_event: str | None = None
    timestamp: str | None = None
    alternatives: list = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self):
        if self.origin not in {
            "legacy",
            "user_report",
            "measurement",
            "external_source",
            "model_proposal",
            "derived",
        }:
            raise ValueError("Unknown origin")
        if self.acceptance not in {
            "unresolved",
            "accepted_for_this_decision",
            "scenario_only",
            "rejected",
        }:
            raise ValueError("Unknown acceptance")
        if self.acceptance == "accepted_for_this_decision" and not self.adoption_event:
            raise ValueError("Adoption requires an identifiable host interaction event")
        if self.origin == "derived" and not self.dependencies:
            raise ValueError("Derived inputs must retain dependency IDs")


@dataclass
class TranslationRecord:
    source_ids: list[str]
    target_field: str
    rule_id: str
    interpretation: str
    unresolved_alternatives: list = field(default_factory=list)
    affected_requirements: list[str] = field(default_factory=list)


@dataclass
class Constraint:
    constraint_id: str
    attribute: str
    operator: str
    limit: Any
    provenance: ConsequentialInput
    scope: str

    def __post_init__(self):
        if self.operator not in {"<=", ">=", "==", "in"}:
            raise ValueError("Unsupported constraint predicate")

    def evaluate(self, option):
        value = option.get(self.attribute)
        if value is None:
            return None
        if isinstance(value, dict):
            if not value.get("evidence_ref") or not {"lower", "upper"} <= value.keys():
                return None
            lo, hi = value["lower"], value["upper"]
            if (
                not all(
                    isinstance(v, (int, float)) and math.isfinite(v) for v in (lo, hi)
                )
                or lo > hi
            ):
                raise PreconditionViolation(
                    "Invalid constraint uncertainty interval", field=self.attribute
                )
            if self.operator not in {"<=", ">="}:
                return None
            lower = self.evaluate({self.attribute: lo})
            upper = self.evaluate({self.attribute: hi})
            return lower if lower == upper else None
        if isinstance(value, float) and not math.isfinite(value):
            raise PreconditionViolation(
                "Constraint value must be finite", field=self.attribute
            )
        try:
            if self.operator == "<=":
                return value <= self.limit
            if self.operator == ">=":
                return value >= self.limit
            if self.operator == "==":
                return value == self.limit
            return value in self.limit
        except TypeError as exc:
            raise PreconditionViolation(
                "Constraint value has incompatible type", field=self.attribute
            ) from exc


@dataclass
class DecisionDescription:
    decision_id: str
    question: str
    revision: int = 1
    problem_types: list[str] = field(default_factory=list)
    options: list = field(default_factory=list)
    actions: list = field(default_factory=list)
    information_types: dict = field(default_factory=dict)
    objectives: list = field(default_factory=list)
    temporal_structure: dict = field(default_factory=dict)
    uncertainties: list = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    unresolved_interpretations: list = field(default_factory=list)
    inputs: dict[str, ConsequentialInput] = field(default_factory=dict)
    translations: list[TranslationRecord] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class Capability:
    job: Job
    problem_types: tuple
    required_facts: tuple
    optional_inputs: tuple
    assumptions: tuple
    outputs: tuple
    limitations: tuple


CAPABILITIES = {
    "static_comparison": Capability(
        Job.MULTIOBJECTIVE,
        ("static_comparison",),
        ("attributes", "scaling_constants", "independence_assumptions"),
        ("alternatives", "constraints", "weight_region"),
        ("scoped independence", "fixed ranges", "supported value scale"),
        ("ranking", "additive weight robustness"),
        ("no causal inference",),
    ),
    "stopping": Capability(
        Job.STOPPING,
        ("stopping",),
        ("horizon", "payoff", "payoff_diverges", "rule-specific prerequisites"),
        ("scores",),
        ("calibrated c01 row",),
        ("threshold", "rule"),
        (
            "no joint recall and rejection",
            "cardinal stopping needs distributional percentiles",
        ),
    ),
    "discounted_mdp": Capability(
        Job.SEQUENTIAL,
        ("discounted_mdp",),
        ("states", "actions", "reward", "transition", "gamma", "markov_verified"),
        ("terminal_states",),
        ("finite bounded Markov model", "infinite discounted horizon"),
        ("greedy policy", "value error bound"),
        ("no finite horizon", "no POMDP planning"),
    ),
    "belief_estimation": Capability(
        Job.SEQUENTIAL,
        ("belief_estimation",),
        ("prior_belief", "observations", "observation_model"),
        (),
        ("likelihood model", "static hidden state"),
        ("posterior belief",),
        (
            "estimation only",
            "no action planning",
        ),
    ),
}


@dataclass
class TranslationResult:
    status: str
    description: DecisionDescription
    contract: InputContract | None
    reasons: list[str]
    next_step: str


def translate_decision(description: DecisionDescription) -> TranslationResult:
    """Translate only host-recorded field interpretations, never classify prose."""
    kinds = description.problem_types
    if len(kinds) != 1 or kinds[0] not in CAPABILITIES:
        return TranslationResult(
            "unsupported_model",
            deepcopy(description),
            None,
            ["No implemented interface composes the requested problem types"],
            "Separate the questions or supply a supported model and interface semantics.",
        )
    values, provenance, reasons = {}, {}, list(description.unresolved_interpretations)
    for record in description.translations:
        if record.target_field not in {
            f.name for f in fields(InputContract)
        } or record.target_field in {
            "job",
            "decision_id",
            "revision",
            "provenance",
            "schema_version",
        }:
            raise ValueError("Invalid translation target")
        if record.target_field in values:
            raise ValueError("Duplicate target interpretation")
        if record.unresolved_alternatives or len(record.source_ids) != 1:
            reasons.append(f"Unresolved translation: {record.target_field}")
            continue
        source = description.inputs.get(record.source_ids[0])
        if source is None:
            reasons.append(f"Missing evidence: {record.target_field}")
            continue
        if source.acceptance == "rejected":
            reasons.append(f"Rejected input: {record.target_field}")
            continue
        values[record.target_field], provenance[record.target_field] = deepcopy(
            source.value
        ), deepcopy(source)
    contract = InputContract(
        job=CAPABILITIES[kinds[0]].job,
        decision_id=description.decision_id,
        revision=description.revision,
        provenance=provenance,
        **values,
    )
    contract.constraints = deepcopy(description.constraints)
    from .elicit import missing_fields

    reasons.extend(f"Missing input: {f}" for f in missing_fields(contract))
    return TranslationResult(
        "unresolved" if reasons else "translated",
        deepcopy(description),
        contract,
        reasons,
        "Resolve consequential interpretations or run a labelled scenario.",
    )


@dataclass
class PreferenceRevision:
    preference_id: str
    previous_revision: int | None
    revision: int
    value: Any
    scope: str
    adoption_event: str | None = None
    reason: str | None = None
    affected_outputs: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.scope not in {
            "exploratory_scenario",
            "adopted_for_this_decision",
            "standing_commitment",
            "suspended",
        }:
            raise ValueError("Unknown preference scope")
        if (
            self.scope
            in {"adopted_for_this_decision", "standing_commitment", "suspended"}
            and not self.adoption_event
        ):
            raise ValueError("Preference adoption or suspension needs a host event")


@dataclass
class DecisionSession:
    decision_id: str
    inputs: dict[str, ConsequentialInput] = field(default_factory=dict)
    history: list[ConsequentialInput] = field(default_factory=list)
    preferences: list[PreferenceRevision] = field(default_factory=list)
    outputs: dict = field(default_factory=dict)

    def record_output(self, output_id, report, dependencies):
        if not set(dependencies) <= self.inputs.keys():
            raise ValueError("Unknown output dependency")
        self.outputs[output_id] = dict(
            report=deepcopy(report), dependencies=list(dependencies), stale=False
        )

    def revise(self, record: ConsequentialInput):
        old = self.inputs.get(record.input_id)
        if old and record.revision != old.revision + 1:
            raise ValueError("Revision must follow the previous revision")
        if old:
            self.history.append(deepcopy(old))
        self.inputs[record.input_id] = deepcopy(record)
        affected = dependency_closure(
            {record.input_id}, {k: v.dependencies for k, v in self.inputs.items()}
        )
        for key in affected - {record.input_id}:
            self.history.append(deepcopy(self.inputs[key]))
            self.inputs[key].acceptance = "unresolved"
        stale = []
        for key, output in self.outputs.items():
            if affected.intersection(output["dependencies"]):
                output["stale"] = True
                report = output["report"]
                report.readiness.state = "blocked"
                report.readiness.reasons.append(
                    "A supporting input was revised; recompute."
                )
                stale.append(key)
        return stale

    def revise_preference(self, revision: PreferenceRevision):
        prior = next(
            (
                p
                for p in reversed(self.preferences)
                if p.preference_id == revision.preference_id
            ),
            None,
        )
        if revision.previous_revision != (prior.revision if prior else None):
            raise ValueError("Preference history does not match")
        old = self.inputs.get(revision.preference_id)
        if revision.revision != (old.revision + 1 if old else 1):
            raise ValueError("Preference revision is not sequential")
        acceptance = {
            "exploratory_scenario": "scenario_only",
            "suspended": "rejected",
        }.get(revision.scope, "accepted_for_this_decision")
        entry = ConsequentialInput(
            revision.preference_id,
            deepcopy(revision.value),
            "user_report",
            revision.adoption_event,
            acceptance,
            self.decision_id,
            revision.revision,
            adoption_event=revision.adoption_event,
        )
        revision = deepcopy(revision)
        revision.affected_outputs = self.revise(entry)
        self.preferences.append(revision)
        return revision.affected_outputs


def encode(value):
    """Tagged JSON-compatible values preserve enum, tuple keys, unknown and false."""
    if isinstance(value, Enum):
        return {"$enum": type(value).__name__, "value": value.value}
    if is_dataclass(value):
        return {
            "$type": type(value).__name__,
            "fields": {f.name: encode(getattr(value, f.name)) for f in fields(value)},
        }
    if isinstance(value, dict):
        return {"$map": [[encode(k), encode(v)] for k, v in value.items()]}
    if isinstance(value, (list, tuple, set, frozenset)):
        return {"$sequence": type(value).__name__, "items": [encode(v) for v in value]}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(
        "Only portable data can be serialized; replace callable models with tables"
    )


def decode(value, *, for_current_use=True):
    if not isinstance(value, dict):
        return value
    from . import contract, report
    from . import robustness, investigation

    registry = {
        c.__name__: c
        for module in (contract, report, robustness, investigation)
        for c in vars(module).values()
        if isinstance(c, type) and (is_dataclass(c) or issubclass(c, Enum))
    }
    registry.update(
        {
            c.__name__: c
            for c in globals().values()
            if isinstance(c, type) and is_dataclass(c)
        }
    )
    if "$enum" in value:
        return registry[value["$enum"]](value["value"])
    if "$map" in value:
        return {
            decode(k, for_current_use=for_current_use): decode(
                v, for_current_use=for_current_use
            )
            for k, v in value["$map"]
        }
    if "$sequence" in value:
        return {"list": list, "tuple": tuple, "set": set, "frozenset": frozenset}[
            value["$sequence"]
        ](decode(v, for_current_use=for_current_use) for v in value["items"])
    if "$type" in value:
        cls = registry[value["$type"]]
        current = for_current_use and cls is not investigation.InvestigationRecord
        data = {
            k: decode(v, for_current_use=current) for k, v in value["fields"].items()
        }
        if data.get("schema_version", 2) > 2:
            raise ValueError("Unsupported future schema")
        result = cls(**data)
        if for_current_use and isinstance(result, report.OutputReport):
            result.readiness.state = "conditional"
            result.readiness.reasons.append(
                "Historical report loaded; recompute for current use."
            )
        if for_current_use and isinstance(result, investigation.Investigation):
            result = result.after_import()
        return result
    raise ValueError("Unrecognized serialized record")


def scenario_branch(
    contract: InputContract, overrides: dict, scenario_id: str
) -> InputContract:
    """A branch is a proposed scenario. It cannot inherit adoption for overrides."""
    result = deepcopy(contract)
    forbidden = {"schema_version", "decision_id", "revision", "provenance"}
    for name, value in overrides.items():
        if name in forbidden or name not in {f.name for f in fields(contract)}:
            raise ValueError("Invalid scenario field")
        setattr(result, name, deepcopy(value))
        old = contract.provenance.get(name)
        result.provenance[name] = ConsequentialInput(
            f"{scenario_id}:{name}",
            deepcopy(value),
            "model_proposal",
            old.evidence_ref if isinstance(old, ConsequentialInput) else None,
            "scenario_only",
            scenario_id,
            dependencies=[old.input_id] if isinstance(old, ConsequentialInput) else [],
        )
    result.revision += 1
    return result


def migrate_legacy_contract(data: dict) -> InputContract:
    """Load a legacy plain contract mapping without inventing historical adoption."""
    from .contract import (
        Horizon,
        Information,
        Payoff,
        RiskAttitude,
        AttributeRange,
        IndependenceAssumption,
    )

    values = deepcopy(data)
    for name, enum in [
        ("job", Job),
        ("horizon", Horizon),
        ("information", Information),
        ("payoff", Payoff),
        ("risk_attitude", RiskAttitude),
    ]:
        if values.get(name) is not None:
            values[name] = enum(values[name])
    if values.get("attributes") is not None:
        values["attributes"] = [
            AttributeRange(**v) if isinstance(v, dict) else v
            for v in values["attributes"]
        ]
    if values.get("independence_assumptions") is not None:
        values["independence_assumptions"] = [
            (
                IndependenceAssumption(
                    **{
                        **v,
                        "subset": frozenset(v["subset"]),
                        "complement": frozenset(v["complement"]),
                    }
                )
                if isinstance(v, dict)
                else v
            )
            for v in values["independence_assumptions"]
        ]
    values["schema_version"] = 2
    values["provenance"] = {
        name: ConsequentialInput(f"legacy:{name}", deepcopy(value))
        for name, value in values.items()
        if name not in {"schema_version", "provenance"}
    }
    return InputContract(**values)


def load_historical_report(data: dict) -> dict:
    """Retain the original artifact, but never reuse its old execution verdict."""
    return dict(
        schema_version=2,
        historical_artifact=deepcopy(data),
        readiness=dict(
            state="conditional",
            reasons=["Historical report: recompute before current use"],
        ),
        analysis_is_complete=False,
    )
