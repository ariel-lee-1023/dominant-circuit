"""Stage 0 evidence-return cycle. Host interpretation is never a formal certificate.

Methods return a new investigation. Records are append-only snapshots; callers keep
and persist the returned state and access payloads through get(), which copies them.
No operation performs collection, contacts people or authorizes an external action.
"""

from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Any
from .evidence import ConsequentialInput, DecisionDescription, encode
from .dependencies import dependency_closure

ASSESSMENTS = {
    "unassessed",
    "supported_within_scope",
    "weakened",
    "contradicted_under_stated_assumptions",
    "unresolved",
}
WORKFLOWS = {
    "drafted",
    "ready_to_observe",
    "awaiting_observation",
    "reviewing",
    "paused",
    "closed_for_current_purpose",
}
CHANGE_TYPES = {
    "input_revision",
    "mechanism_revision",
    "boundary_revision",
    "goal_revision",
    "measurement_correction",
    "unresolved_evidence",
}


@dataclass(frozen=True)
class Boundary:
    included: tuple[str, ...]
    external: tuple[str, ...]
    unknown_or_omitted: tuple[str, ...]
    omission_check: str
    visible_observations: tuple[str, ...] = ()
    possible_interventions: tuple[str, ...] = ()
    outside_observation: str | None = None
    outside_access: str = "unknown"


@dataclass(frozen=True)
class WorkingAccount:
    name: str
    variables: tuple[str, ...]
    boundary: Boundary
    mechanisms: tuple[str, ...]
    proposed_by: str | None = None
    assessment: str = "unassessed"
    assessment_scope: str = ""
    evidence_refs: tuple[str, ...] = ()
    working_use_event: str | None = None

    def __post_init__(self):
        if not self.name or self.assessment not in ASSESSMENTS:
            raise ValueError("Account needs a name and valid assessment")
        if not self.boundary.omission_check:
            raise ValueError(
                "Record a compact omission check or explain why no consequential omission was identified"
            )


@dataclass(frozen=True)
class AccountRelationship:
    accounts: tuple[str, ...]
    relationship: str
    explanation: str

    def __post_init__(self):
        if (
            self.relationship
            not in {"competing", "complementary", "alternative_boundary", "unresolved"}
            or len(self.accounts) < 2
            or not self.explanation
        ):
            raise ValueError("Specify related accounts, relationship and explanation")


@dataclass(frozen=True)
class PossibleFinding:
    finding_id: str
    description: str
    implication: str


@dataclass(frozen=True)
class ObservationPlan:
    question: str
    kind: str
    accounts: tuple[str, ...]
    assumptions: tuple[str, ...]
    source: str
    method: str
    possible_findings: tuple[PossibleFinding, ...]
    access: str = "unknown"
    owner: str | None = None
    effort: str | None = None
    delay: str | None = None
    collection_effects: str | None = None
    omission_challenge: str | None = None
    effort_assessment: str = "unknown"
    authorization_event: str | None = None
    authorizer: str | None = None

    def __post_init__(self):
        if self.kind not in {"exploratory", "discriminating", "descriptive"}:
            raise ValueError("Unknown observation kind")
        if self.access not in {
            "available",
            "unavailable",
            "unknown",
        } or self.effort_assessment not in {
            "manageable",
            "disproportionate",
            "unknown",
        }:
            raise ValueError("Invalid feasibility assessment")
        if not self.question or not self.source or not self.method:
            raise ValueError("Observation plans need a question, source and method")
        codes = [f.finding_id for f in self.possible_findings]
        if len(set(codes)) != len(codes) or "inconclusive" not in codes:
            raise ValueError(
                "Plan needs distinct findings including an inconclusive next step"
            )
        if any(not f.description or not f.implication for f in self.possible_findings):
            raise ValueError("Each possible finding needs its meaning and implication")
        if self.kind == "discriminating" and (
            not self.accounts or not self.assumptions or len(codes) < 2
        ):
            raise ValueError(
                "Discriminating plans must identify accounts, assumptions and meaningful outcomes"
            )
        if bool(self.authorization_event) != bool(self.authorizer):
            raise ValueError(
                "Authorization requires both an event and an attributed authorizer"
            )

    @property
    def feasible(self):
        return self.access == "available" and self.effort_assessment == "manageable"


@dataclass(frozen=True)
class Observation:
    finding: ConsequentialInput
    context: str
    missingness: tuple[str, ...] = ()
    selection_limits: tuple[str, ...] = ()
    raw_episode_ref: str | None = None
    plan_ref: str | None = None
    reported_by: str | None = None
    obtained: bool = True

    def __post_init__(self):
        if (
            not self.obtained
            or self.finding.origin
            not in {"user_report", "measurement", "external_source"}
            or not self.finding.evidence_ref
            or not self.context
        ):
            raise ValueError(
                "Obtained observations need an actual source event, context and reported evidence, not a proposed finding"
            )
        if self.finding.value is None and not self.missingness:
            raise ValueError(
                "Explain missingness rather than treating absent evidence as a negative finding"
            )


@dataclass(frozen=True)
class AnalyticalResult:
    target: str
    method: str
    applicability: str
    result: str
    analysis_type: str = "structural"
    reason: str = ""
    status: str = "qualitative"
    model_spec: str | None = None
    observable_set: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    external_certificate_ref: str | None = None

    def __post_init__(self):
        if self.applicability not in {"relevant", "inapplicable", "unresolved"}:
            raise ValueError("Unknown applicability")
        if self.status not in {"qualitative", "unresolved", "external_unverified"}:
            raise ValueError(
                "This library implements no formal identification or stability verifier; formal claims must remain external_unverified"
            )
        if not self.target or not self.method or not self.result:
            raise ValueError("Specify target, method and result or unresolved limit")
        if self.applicability != "relevant" and not self.reason:
            raise ValueError("Explain inapplicability or unresolved applicability")
        if self.status == "external_unverified":
            if not self.external_certificate_ref or not self.model_spec:
                raise ValueError(
                    "External assessments need a specified model and certificate reference"
                )
            if self.analysis_type == "identification" and not self.observable_set:
                raise ValueError("Identification requires the observable set")


@dataclass(frozen=True)
class ParticipantPosition:
    participant: str
    goal: str
    agreement: str = "unresolved"
    proposed_account: str | None = None
    affected: bool | None = None
    can_access: bool | None = None
    can_authorize: bool | None = None
    role: str | None = None

    def __post_init__(self):
        if (
            self.agreement not in {"unresolved", "disputed", "adopted"}
            or not self.participant
            or not self.goal
        ):
            raise ValueError(
                "Position must retain participant, goal and scoped agreement"
            )


@dataclass(frozen=True)
class InvestigationRecord:
    kind: str
    provenance: ConsequentialInput
    payload: Any
    dependencies: tuple[str, ...] = ()

    @property
    def ref(self):
        return f"{self.kind}:{self.provenance.input_id}@{self.provenance.revision}"


@dataclass(frozen=True)
class InvestigationRevision:
    previous_refs: tuple[str, ...]
    new_refs: tuple[str, ...]
    trigger_ref: str
    change_types: tuple[str, ...]
    reason: str
    invalidated_refs: tuple[str, ...]
    unresolved_alternatives: tuple[str, ...] = ()


@dataclass(frozen=True)
class InvestigationHandoff:
    contract: Any
    model_refs: tuple[str, ...]
    goal_ref: str
    description: DecisionDescription
    status: str
    completed_checks: tuple[str, ...]
    unresolved_conditions: tuple[str, ...]
    return_conditions: tuple[str, ...]


@dataclass(frozen=True)
class Investigation:
    investigation_id: str
    records: tuple[InvestigationRecord, ...] = ()
    revisions: tuple[InvestigationRevision, ...] = ()
    current_model_ref: str | None = None
    current_goal_ref: str | None = None
    workflow: str = "drafted"
    next_step: str = ""
    unresolved_questions: tuple[str, ...] = ()
    pause_reason: str | None = None
    reopening_trigger: str | None = None
    pending_reviews: tuple[str, ...] = ()
    stale_refs: tuple[str, ...] = ()
    selected_plan_ref: str | None = None
    scenario_id: str | None = None
    schema_version: int = 2

    def __post_init__(self):
        if not self.investigation_id or self.workflow not in WORKFLOWS:
            raise ValueError("Invalid investigation ID or workflow")
        refs = {r.ref for r in self.records}
        if len(refs) != len(self.records):
            raise ValueError("Revision references must be unique")
        seen = set()
        for record in self.records:
            if not set(record.dependencies) <= seen:
                raise ValueError(
                    "Dependencies must name earlier records; cycles and forward references are invalid"
                )
            seen.add(record.ref)
        if self.current_goal_ref and self.current_goal_ref not in refs:
            raise ValueError("Unknown goal pointer")
        if self.current_model_ref and self.current_model_ref not in refs:
            raise ValueError("Unknown model pointer")
        if self.workflow in {"ready_to_observe", "awaiting_observation"}:
            if (
                not self.selected_plan_ref
                or not self.is_valid(self.selected_plan_ref)
                or self.pending_reviews
            ):
                raise ValueError(
                    "Observation readiness requires a current selected plan and no pending evidence review"
                )
            plan = self.get(self.selected_plan_ref)
            if not isinstance(plan, ObservationPlan) or not plan.feasible:
                raise ValueError(
                    "Observation readiness requires feasible access and effort"
                )
            if self.workflow == "awaiting_observation" and not plan.authorization_event:
                raise ValueError(
                    "Awaiting collection requires an attributed authorization event"
                )
        if self.workflow == "paused" and (
            not self.pause_reason or not self.reopening_trigger
        ):
            raise ValueError(
                "Paused investigations need a reason and reopening trigger"
            )

    @classmethod
    def begin(cls, investigation_id, description, event):
        if description.decision_id != investigation_id:
            raise ValueError("Description must name the same investigation/decision")
        state = cls(investigation_id)
        state = state._append("goal", "purpose", description, event)
        return replace(state, current_goal_ref=state.latest_ref("goal", "purpose"))

    def _record(self, ref):
        for record in self.records:
            if record.ref == ref:
                return record
        raise ValueError(f"Unknown investigation reference: {ref}")

    def get(self, ref):
        return deepcopy(self._record(ref).payload)

    def latest_ref(self, kind, name):
        found = [
            r.ref
            for r in self.records
            if r.kind == kind and r.provenance.input_id == name
        ]
        if not found:
            raise ValueError(f"No {kind} record: {name}")
        return found[-1]

    def _current(self, kind):
        return [
            r
            for r in self.records
            if r.kind == kind and self.latest_ref(kind, r.provenance.input_id) == r.ref
        ]

    def is_valid(self, ref):
        record = self._record(ref)
        return (
            ref not in self.stale_refs
            and self.latest_ref(record.kind, record.provenance.input_id) == ref
            and all(self.is_valid(dep) for dep in record.dependencies)
        )

    def _affected(self, refs):
        return dependency_closure(refs, {r.ref: r.dependencies for r in self.records})

    def _invalidate(self, refs):
        stale = tuple(sorted(set(self.stale_refs) | self._affected(refs)))
        workflow = self.workflow
        if self.selected_plan_ref in stale and workflow in {
            "ready_to_observe",
            "awaiting_observation",
        }:
            workflow = "reviewing" if self.pending_reviews else "drafted"
        return replace(self, stale_refs=stale, workflow=workflow)

    def _append(
        self,
        kind,
        name,
        payload,
        event,
        dependencies=(),
        origin="user_report",
        provenance=None,
    ):
        if not event:
            raise ValueError("An identifiable source or interaction event is required")
        for dep in dependencies:
            self._record(dep)
        previous = [
            r for r in self.records if r.kind == kind and r.provenance.input_id == name
        ]
        revision = previous[-1].provenance.revision + 1 if previous else 1
        evidence = (
            deepcopy(provenance)
            if provenance
            else ConsequentialInput(
                name,
                deepcopy(payload),
                origin,
                event,
                scope=self.investigation_id,
                dependencies=list(dependencies),
            )
        )
        evidence.input_id = name
        evidence.revision = revision
        evidence.dependencies = list(dependencies)
        node = InvestigationRecord(
            kind, evidence, deepcopy(payload), tuple(dependencies)
        )
        state = self._invalidate((previous[-1].ref,)) if previous else self
        return replace(state, records=state.records + (node,))

    def _log(self, previous, new, trigger, types, reason, prior_stale=()):
        if not trigger or not reason or not types or not set(types) <= CHANGE_TYPES:
            raise ValueError(
                "A revision needs a trigger, valid change types and a reason"
            )
        revision = InvestigationRevision(
            tuple(previous),
            tuple(new),
            trigger,
            tuple(types),
            reason,
            tuple(sorted(set(self.stale_refs) - set(prior_stale))),
            self.unresolved_questions,
        )
        return replace(self, revisions=self.revisions + (revision,))

    def propose_account(self, name, account, event):
        if any(
            r.kind == "account" and r.provenance.input_id == name for r in self.records
        ):
            raise ValueError("Use revise_account to retain an explicit revision reason")
        if account.assessment != "unassessed":
            raise ValueError(
                "A proposed account starts unassessed; it is not an observed result"
            )
        state = self._append("account", name, account, event, origin="model_proposal")
        state = state._invalidate(
            [r.ref for r in self.records if r.kind in {"handoff", "report"}]
        )
        return replace(
            state,
            current_model_ref=state.latest_ref("account", name),
            workflow="drafted",
        )

    def relate_accounts(self, name, relationship, event):
        for ref in relationship.accounts:
            if self._record(ref).kind != "account" or not self.is_valid(ref):
                raise ValueError("Relationships must identify current accounts")
        return self._append(
            "relationship",
            name,
            relationship,
            event,
            relationship.accounts,
            origin="model_proposal",
        )

    def propose_observation(self, name, plan, event):
        if any(
            self._record(ref).kind != "account" or not self.is_valid(ref)
            for ref in plan.accounts
        ):
            raise ValueError("Observation plans must address current account revisions")
        if plan.authorization_event:
            raise ValueError(
                "A proposed observation cannot already claim collection authorization"
            )
        dependencies = tuple(dict.fromkeys((self.current_goal_ref,) + plan.accounts))
        state = self._append(
            "plan", name, plan, event, dependencies, origin="model_proposal"
        )
        ref = state.latest_ref("plan", name)
        return replace(
            state,
            selected_plan_ref=ref,
            next_step=plan.question,
            workflow=(
                "reviewing"
                if state.pending_reviews
                else "ready_to_observe" if plan.feasible else "drafted"
            ),
        )

    def await_observation(self, name, authorizer, authorization_event):
        ref = self.latest_ref("plan", name)
        plan = self.get(ref)
        if self.pending_reviews or not self.is_valid(ref) or not plan.feasible:
            raise ValueError(
                "Only a current, feasible observation can await collection"
            )
        for record in self._current("position"):
            if (
                record.payload.participant == authorizer
                and record.payload.can_authorize is False
            ):
                raise ValueError("Recorded participant lacks collection authority")
        plan = replace(
            plan, authorizer=authorizer, authorization_event=authorization_event
        )
        state = self._append(
            "plan",
            name,
            plan,
            authorization_event,
            self._record(ref).dependencies,
            origin="model_proposal",
        )
        return replace(
            state,
            workflow="awaiting_observation",
            selected_plan_ref=state.latest_ref("plan", name),
        )

    def receive_observation(self, name, observation):
        if any(r.kind == "obs" and r.provenance.input_id == name for r in self.records):
            raise ValueError("Use correct_observation to retain measurement history")
        observation.__post_init__()
        plan = self.get(observation.plan_ref) if observation.plan_ref else None
        if plan is not None and not isinstance(plan, ObservationPlan):
            raise ValueError("Observation must refer to a proposed plan")
        state = self._append(
            "obs",
            name,
            observation,
            observation.finding.evidence_ref,
            provenance=observation.finding,
        )
        ref = state.latest_ref("obs", name)
        # Raw observations are retained independently of whether their old plan is stale.
        targets = (
            tuple(
                self.latest_ref("account", self._record(ref).provenance.input_id)
                for ref in plan.accounts
            )
            if plan
            else tuple(r.ref for r in self._current("account"))
        )
        derived = [
            r.ref
            for r in self.records
            if r.kind in {"analysis", "handoff", "report"}
            and (not targets or set(r.dependencies) & set(self._affected(targets)))
        ]
        state = state._invalidate(derived)
        return replace(
            state,
            pending_reviews=state.pending_reviews + (ref,),
            workflow="reviewing",
            next_step="Review the returned evidence against the earlier plan; unresolved evidence is allowed.",
        )

    def review_observation(
        self, name, finding_id, assessments, change_types, reason, event
    ):
        obs_ref = self.latest_ref("obs", name)
        if obs_ref not in self.pending_reviews:
            raise ValueError("Observation is not awaiting review")
        obs = self.get(obs_ref)
        plan = self.get(obs.plan_ref) if obs.plan_ref else None
        possible = {f.finding_id: f for f in plan.possible_findings} if plan else {}
        if plan and finding_id not in possible:
            raise ValueError(
                "Compare with an anticipated finding, including inconclusive"
            )
        if not plan and finding_id != "inconclusive":
            raise ValueError(
                "Unplanned evidence needs explicit unresolved review before a new test"
            )
        if "goal_revision" in change_types:
            raise ValueError(
                "Empirical review cannot silently revise the goal; use revise_goal"
            )
        states = set(assessments.values())
        if not states <= ASSESSMENTS | {"unchanged", "not_assessed"}:
            raise ValueError("Unknown assessment effect")
        if (obs.finding.value is None or finding_id == "inconclusive") and states & {
            "supported_within_scope",
            "contradicted_under_stated_assumptions",
        }:
            raise ValueError(
                "Missing or inconclusive observations cannot establish support or contradiction"
            )
        if (
            plan
            and plan.kind != "discriminating"
            and "contradicted_under_stated_assumptions" in states
        ):
            raise ValueError(
                "An exploratory observation is not a discriminating falsification test"
            )
        state = self
        previous, new = [], []
        for account_name, assessment in assessments.items():
            ref = state.latest_ref("account", account_name)
            if plan and account_name not in {
                self._record(r).provenance.input_id for r in plan.accounts
            }:
                raise ValueError("Plan did not assess this account")
            if assessment in {"unchanged", "not_assessed"}:
                continue
            account = replace(
                state.get(ref),
                assessment=assessment,
                assessment_scope=reason,
                evidence_refs=state.get(ref).evidence_refs + (obs_ref,),
            )
            # Evidence references on an account carry assessment dependencies without
            # depending on its prior account version, which is now historical.
            state = state._append(
                "account",
                account_name,
                account,
                event,
                tuple(dict.fromkeys(account.evidence_refs)),
                origin="derived",
            )
            current = state.latest_ref("account", account_name)
            if self.current_model_ref == ref:
                state = replace(state, current_model_ref=current)
            previous.append(ref)
            new.append(current)
        review = dict(
            observation_ref=obs_ref,
            plan_ref=obs.plan_ref,
            finding_id=finding_id,
            anticipated_implication=(
                possible[finding_id].implication
                if plan
                else "Retain the episode and clarify a possible mismatch"
            ),
            assessments=deepcopy(assessments),
            reason=reason,
        )
        state = state._append(
            "review", name, review, event, (obs_ref,), origin="derived"
        )
        state = state._log(
            previous, new, obs_ref, change_types, reason, self.stale_refs
        )
        pending = tuple(r for r in state.pending_reviews if r != obs_ref)
        return replace(
            state,
            pending_reviews=pending,
            workflow="reviewing" if pending else "drafted",
            next_step=review["anticipated_implication"],
            unresolved_questions=tuple(
                dict.fromkeys(
                    state.unresolved_questions
                    + ((reason,) if finding_id == "inconclusive" else ())
                )
            ),
        )

    def revise_account(self, name, account, change_types, trigger_ref, reason):
        if "goal_revision" in change_types:
            raise ValueError("Goal revisions do not falsify accounts")
        self._record(trigger_ref)
        ref = self.latest_ref("account", name)
        if account.assessment != "unassessed":
            raise ValueError("A revised mechanism or boundary starts unassessed")
        state = self._append(
            "account",
            name,
            account,
            trigger_ref,
            (trigger_ref,),
            origin="model_proposal",
        )
        new = state.latest_ref("account", name)
        state = state._log(
            (ref,), (new,), trigger_ref, change_types, reason, self.stale_refs
        )
        return replace(
            state,
            current_model_ref=(
                new if self.current_model_ref == ref else self.current_model_ref
            ),
            workflow="reviewing" if state.pending_reviews else "drafted",
            next_step="Select a useful observation under the revised account.",
        )

    def revise_goal(self, description, event, reason):
        if description.decision_id != self.investigation_id:
            raise ValueError("Goal belongs to another decision")
        old = self.current_goal_ref
        description = deepcopy(description)
        description.revision = self._record(old).provenance.revision + 1
        state = self._append("goal", "purpose", description, event)
        new = state.latest_ref("goal", "purpose")
        state = state._log(
            (old,), (new,), event, ("goal_revision",), reason, self.stale_refs
        )
        return replace(
            state,
            current_goal_ref=new,
            workflow="reviewing" if state.pending_reviews else "drafted",
            next_step="Reassess observations and recommendations for the revised goal.",
        )

    def correct_observation(self, name, observation, event, reason):
        old = self.latest_ref("obs", name)
        observation.__post_init__()
        state = self._append(
            "obs", name, observation, event, provenance=observation.finding
        )
        new = state.latest_ref("obs", name)
        # The correction can also challenge analyses that used the model rather than
        # naming the earlier measurement directly.
        state = state._invalidate(
            [
                r.ref
                for r in state.records
                if r.kind in {"analysis", "handoff", "report"}
            ]
        )
        state = state._log(
            (old,), (new,), event, ("measurement_correction",), reason, self.stale_refs
        )
        return replace(
            state,
            workflow="reviewing",
            pending_reviews=tuple(r for r in state.pending_reviews if r != old)
            + (new,),
            next_step="Revisit measurement comparability before retaining the causal interpretation.",
        )

    def record_analysis(self, name, analysis, dependencies, event):
        analysis.__post_init__()
        for ref in dependencies:
            if not self.is_valid(ref):
                raise ValueError("Analysis refers to stale inputs")
        deps = tuple(dict.fromkeys((self.current_goal_ref,) + tuple(dependencies)))
        return self._append("analysis", name, analysis, event, deps, origin="derived")

    def record_correction(self, name, kind, text, participant, event):
        if (
            kind
            not in {
                "counterexample",
                "missing_factor",
                "disputed_interpretation",
                "different_goal",
                "uncertainty",
            }
            or not text
        ):
            raise ValueError("Preserve a concrete correction or uncertainty")
        state = self._append(
            "correction",
            name,
            dict(kind=kind, text=text, participant=participant),
            event,
        )
        ref = state.latest_ref("correction", name)
        state = state._invalidate(
            [
                r.ref
                for r in state.records
                if r.kind in {"analysis", "handoff", "report"}
            ]
        )
        return replace(
            state,
            workflow="reviewing",
            pending_reviews=state.pending_reviews + (ref,),
            unresolved_questions=state.unresolved_questions + (text,),
            next_step="Review the concrete correction; no graph editing is required.",
        )

    def acknowledge_correction(self, name, reason, event):
        if not reason:
            raise ValueError(
                "Explain the mismatch, unresolved interpretation or justified next step"
            )
        ref = self.latest_ref("correction", name)
        if ref not in self.pending_reviews:
            raise ValueError("Correction is not pending")
        state = self._append(
            "correction_review",
            name,
            dict(correction_ref=ref, reason=reason),
            event,
            (ref,),
            origin="derived",
        )
        pending = tuple(r for r in state.pending_reviews if r != ref)
        return replace(
            state,
            pending_reviews=pending,
            workflow="reviewing" if pending else "drafted",
            next_step=reason,
        )

    def record_position(self, name, position, event):
        state = self._append("position", name, position, event)
        state = state._invalidate(
            [r.ref for r in state.records if r.kind in {"handoff", "report"}]
        )
        return state

    @property
    def positions(self):
        return tuple(deepcopy(r.payload) for r in self._current("position"))

    @property
    def contested_goals(self):
        return bool(self.positions) and (
            any(p.agreement != "adopted" for p in self.positions)
            or len({p.goal for p in self.positions}) > 1
        )

    @property
    def accounts(self):
        return tuple(deepcopy(r.payload) for r in self._current("account"))

    @property
    def relationships(self):
        return tuple(deepcopy(r.payload) for r in self._current("relationship"))

    @property
    def observations(self):
        return tuple(deepcopy(r.payload) for r in self._current("obs"))

    def pause(self, reason, reopening_trigger, event):
        if not reason or not reopening_trigger:
            raise ValueError("Pause needs a reason and reopening trigger")
        state = self._append(
            "workflow",
            str(len(self.records)),
            dict(state="paused", reason=reason),
            event,
        )
        return replace(
            state,
            workflow="paused",
            pause_reason=reason,
            reopening_trigger=reopening_trigger,
            next_step="Paused: " + reason,
        )

    def reopen(self, event):
        if self.workflow not in {"paused", "closed_for_current_purpose"}:
            raise ValueError("Investigation is not paused or closed")
        state = self._append(
            "workflow", str(len(self.records)), dict(state="reopened"), event
        )
        return replace(
            state,
            workflow="reviewing" if state.pending_reviews else "drafted",
            pause_reason=None,
            next_step="Resume from current valid revisions; reassess access and stale plans.",
        )

    def close_cycle(self, reason, event):
        if self.pending_reviews or not self.next_step or not reason:
            raise ValueError(
                "A cycle needs reviewed evidence and a justified next step"
            )
        state = self._append(
            "workflow",
            str(len(self.records)),
            dict(state="closed_for_current_purpose", reason=reason),
            event,
        )
        return replace(
            state,
            workflow="closed_for_current_purpose",
            reopening_trigger="New evidence, changed goal, access or boundary conditions",
        )

    def handoff(self, name, contract, unresolved_conditions=(), analysis_refs=()):
        from .dispatch import dispatch

        conditions = list(unresolved_conditions)
        if self.pending_reviews:
            conditions.append("Evidence or user correction is awaiting review")
        if self.contested_goals:
            conditions.append("Participant goals remain contested")
        if self.scenario_id:
            conditions.append("Scenario branch has no adopted current handoff")
        refs = tuple(r.ref for r in self._current("account"))
        if any(not self.is_valid(ref) for ref in refs + tuple(analysis_refs)):
            conditions.append("A model assessment or analytical dependency is stale")
        contract = deepcopy(contract)
        if contract.decision_id not in {None, "legacy", self.investigation_id}:
            raise ValueError("Contract belongs to another decision")
        contract.decision_id = self.investigation_id
        contract.revision = self._record(self.current_goal_ref).provenance.revision
        if self.workflow == "paused":
            conditions.append("Investigation is paused")
        if contract.investigation_id is not None:
            raise ValueError(
                "Translate a fresh contract rather than reusing an old handoff"
            )
        try:
            report = dispatch(contract.job, contract)
            checks = tuple(report.readiness.completed_checks)
        except (ValueError, TypeError) as exc:
            conditions.append(str(exc))
            checks = ()
        except Exception as exc:
            from .errors import DominantCircuitError

            if not isinstance(exc, DominantCircuitError):
                raise
            conditions.append(str(exc))
            checks = ()
        previous = [
            r
            for r in self.records
            if r.kind == "handoff" and r.provenance.input_id == name
        ]
        ref = f"handoff:{name}@{len(previous)+1}"
        contract.investigation_id = self.investigation_id
        contract.investigation_handoff_ref = ref
        handoff = InvestigationHandoff(
            contract,
            refs,
            self.current_goal_ref,
            self.get(self.current_goal_ref),
            "unresolved" if conditions else "solver_ready",
            checks,
            tuple(conditions),
            (
                "Return when evidence, measurement, boundary, goal, access or assumptions change.",
            ),
        )
        deps = tuple(
            dict.fromkeys((self.current_goal_ref,) + refs + tuple(analysis_refs))
        )
        state = self._append(
            "handoff",
            name,
            handoff,
            self._record(self.current_goal_ref).provenance.evidence_ref,
            deps,
            origin="derived",
        )
        return replace(
            state,
            next_step="Solver handoff "
            + handoff.status
            + "; recommendation readiness remains separate.",
        )

    def validate_handoff(self, contract):
        if contract.investigation_id != self.investigation_id:
            raise ValueError("Handoff belongs to another investigation")
        ref = contract.investigation_handoff_ref
        if (
            self.pending_reviews
            or self.contested_goals
            or self.workflow == "paused"
            or not self.is_valid(ref)
        ):
            raise ValueError(
                "Investigation handoff is stale or awaiting review; return to Stage 0"
            )
        handoff = self.get(ref)
        if handoff.status != "solver_ready" or encode(handoff.contract) != encode(
            contract
        ):
            raise ValueError("Handoff is unresolved or its bound contract was changed")
        return handoff

    def get_handoff(self, name):
        contract = self.get(self.latest_ref("handoff", name)).contract
        self.validate_handoff(contract)
        return contract

    def record_report(self, name, report, handoff_name, event):
        ref = self.latest_ref("handoff", handoff_name)
        self.get_handoff(handoff_name)
        if (
            report.computation.get("investigation_handoff_ref") != ref
            or report.computation.get("investigation_id") != self.investigation_id
        ):
            raise ValueError("Report does not belong to this investigation handoff")
        return self._append("report", name, report, event, (ref,), origin="derived")

    def get_report(self, name):
        ref = self.latest_ref("report", name)
        report = self.get(ref)
        if self.pending_reviews or not self.is_valid(ref):
            report.readiness.state = "blocked"
            report.readiness.reasons.append(
                "Investigation evidence or dependencies changed; revalidate the handoff."
            )
        return report

    def branch(self, scenario_id):
        if not scenario_id:
            raise ValueError("Name the scenario branch")
        state = self._invalidate(
            [r.ref for r in self.records if r.kind in {"handoff", "report"}]
        )
        return replace(
            state,
            scenario_id=scenario_id,
            workflow="drafted",
            selected_plan_ref=None,
            next_step="Explore this scenario; prior collection authorization and handoff readiness do not transfer.",
        )

    def after_import(self):
        return self._invalidate(
            [r.ref for r in self.records if r.kind in {"handoff", "report"}]
        )

    def last_update(self):
        if not self.revisions:
            return "What changed: no reviewed revision yet. Next: " + self.next_step
        r = self.revisions[-1]
        return f'What changed: {", ".join(r.change_types)}. Why: {r.reason}. Unresolved: {"; ".join(self.unresolved_questions) or "scope and interpretation limits remain"}. Next: {self.next_step}'

    def render_fields(self):
        models = []
        for record in self._current("account"):
            account = record.payload
            status = (
                account.assessment
                if self.is_valid(record.ref)
                else "unresolved (stale assessment)"
            )
            mechanisms = "; ".join(account.mechanisms)
            included = ", ".join(account.boundary.included) or "none specified"
            external = ", ".join(account.boundary.external) or "none specified"
            omitted = (
                ", ".join(account.boundary.unknown_or_omitted) or "none identified"
            )
            scope = account.assessment_scope or "not yet assessed"
            models.append(
                f"{account.name}: {mechanisms}. Includes {included}; "
                f"external {external}; omitted/unknown {omitted}. "
                f"{account.boundary.omission_check} Assessment: {status}. Scope: {scope}."
            )
            if account.boundary.visible_observations:
                models.append(
                    "Visible observations: "
                    + ", ".join(account.boundary.visible_observations)
                    + "."
                )
            if account.boundary.possible_interventions:
                models.append(
                    "Possible interventions to investigate, not authorized actions: "
                    + ", ".join(account.boundary.possible_interventions)
                    + "."
                )
            if account.boundary.outside_observation:
                models.append(
                    "Outside-boundary observation: "
                    + account.boundary.outside_observation
                    + "; access "
                    + account.boundary.outside_access
                    + "."
                )
        plan = self.get(self.selected_plan_ref) if self.selected_plan_ref else None
        if self.workflow == "paused":
            observation = (
                f"Paused: {self.pause_reason}. Reopen when {self.reopening_trigger}."
            )
        elif plan and self.is_valid(self.selected_plan_ref):
            observation = f'{self.workflow}: suggested {plan.kind} observation: {plan.question}. Method: {plan.method}. Source: {plan.source}. Access: {plan.access}; effort: {plan.effort or "unknown"}; delay: {plan.delay or "unknown"}; owner: {plan.owner or "unknown"}. {plan.collection_effects or "Collection effects unknown"}. This plan does not authorize external action.'
        else:
            observation = (
                self.next_step
                or "No observation is necessary for a sufficiently specified static comparison."
            )
        positions = "; ".join(
            f"{p.participant}: {p.goal} ({p.agreement})" for p in self.positions
        )
        limits = [
            "Model limits describe unanswered questions, not questions the user is forbidden to ask.",
            "No formal causal identification or stability result is established by completing this record.",
        ]
        for obs in self.observations:
            limits.extend(obs.missingness + obs.selection_limits)
        if self.pending_reviews:
            limits.append("Returned evidence or correction still awaits review.")
        if self.contested_goals:
            limits.append("Goals remain contested; no consensus was inferred.")
        for record in self._current("analysis"):
            a = record.payload
            limits.append(
                f'{a.target}: {a.applicability}, {a.status if self.is_valid(record.ref) else "stale"}; {a.reason or a.result}'
            )
        rivals = "; ".join(
            f"{r.payload.relationship}: {r.payload.explanation}"
            + (" (relationship needs review)" if not self.is_valid(r.ref) else "")
            for r in self._current("relationship")
        )
        findings = (
            "; ".join(
                f"{f.description}: {f.implication}" for f in plan.possible_findings
            )
            if plan and self.is_valid(self.selected_plan_ref)
            else "Reopen on consequential new evidence, a counterexample or a changed goal; revise any stale observation plan."
        )
        return {
            "starting_model": " ".join(models)
            or self.get(self.current_goal_ref).question,
            "observation_instruction": observation,
            "commitments": positions
            or "Working accounts are proposals; scoped use does not establish factual truth or a standing commitment.",
            "prohibitions_limits": " ".join(limits),
            "overturn_conditions": findings,
            "rival_models": rivals
            or "No additional account is needed merely to fill a quota.",
        }

    def to_markdown(self):
        labels = {
            "starting_model": "Starting model",
            "observation_instruction": "Observation instruction",
            "commitments": "Commitments",
            "prohibitions_limits": "Prohibitions/limits",
            "overturn_conditions": "Overturn conditions",
            "rival_models": "Rival models",
        }
        return "\n\n".join(
            f"## {labels[key]}\n\n{value}"
            for key, value in self.render_fields().items()
        )


def migrate_stage0_snapshot(fields):
    """Preserve older six-field outputs as artifacts with unknown history."""
    return {
        "schema_version": 2,
        "historical_snapshot": deepcopy(fields),
        "investigation_history": "unknown",
        "workflow": "drafted",
        "assessment": "unassessed",
        "observations": [],
        "handoff_status": "unresolved",
        "next_step": "Create a current investigation; do not invent past observations or adoption.",
    }
