"""Output Contract — six mandatory fields."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class InvariantResult:
    invariant_id: str
    name: str
    passed: bool
    residual: Optional[float] = None
    tolerance: Optional[float] = None
    message: str = ""


@dataclass
class AuditResult:
    results: list[InvariantResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failures(self) -> list[InvariantResult]:
        return [r for r in self.results if not r.passed]


@dataclass
class SensitivityEntry:
    assumption: str
    perturbation: str
    new_decision: Any
    decision_changed: bool
    fragility: str


# Orders in the zero-order expansion (零阶展开). These are not severity labels;
# they are structural claims about how a term relates to the trunk.
ORDER_ZERO = "zero"          # 零阶道理 — the trunk itself
ORDER_FIRST = "first"        # 一阶修正 — refines the trunk, cannot overturn it
ORDER_OVERTURN = "overturn"  # 翻盘项 — a DIFFERENT trunk, not a correction
ORDER_HARD = "hard"          # 硬约束 — no trunk exists; veto
ORDER_DROPPED = "dropped"    # 舍去项 — thrown away by 主导平衡 as non-dominant

_ORDER_GLOSS = {
    ORDER_ZERO: "零阶 · trunk",
    ORDER_FIRST: "一阶修正 · refines, cannot overturn",
    ORDER_OVERTURN: "翻盘 · different zero-order model",
    ORDER_HARD: "硬约束 · no zero-order exists",
    ORDER_DROPPED: "舍去项 · dropped as non-dominant",
}


@dataclass
class PerturbationTerm:
    """One term in the zero-order expansion of a decision.

    The distinction that matters is `first` vs `overturn`, and it is decided
    structurally, not by a magnitude threshold: a term is a *correction* when it
    refines the same underlying model, and an *overturn* when it moves the problem
    to a different calibrated model — a different row of the corpus decision table.
    A 65% shift that stays in one model is still a correction; a 5% shift that
    changes models is still an overturn.

    `relative_shift` is the SIGNED (value - zero_order) / |zero_order| where the two
    are numerically comparable, and None otherwise. It is reported for judgement,
    never used for classification.
    """
    order: str                              # ORDER_ZERO | ORDER_FIRST | ORDER_OVERTURN | ORDER_HARD
    label: str
    value: Any
    citation: str
    relative_shift: Optional[float] = None
    note: str = ""

    @property
    def gloss(self) -> str:
        return _ORDER_GLOSS.get(self.order, self.order)


def relative_shift(value: Any, zero_order: Any) -> Optional[float]:
    """Signed (value - base) / |base|, when both are real and the base is non-zero.

    Signed, so a term that moves the decision *down* reads as negative rather than
    as an indistinguishable magnitude.
    """
    try:
        base = float(zero_order)
        if base == 0.0:
            return None
        return (float(value) - base) / abs(base)
    except (TypeError, ValueError):
        return None


@dataclass
class OutputReport:
    decision: Any
    formula_name: str
    formula_latex: str
    citation: str
    numeric: dict[str, float]
    assumptions: dict[str, Any]
    sensitivity: list[SensitivityEntry]
    audit: AuditResult
    # Stage 5: the decision restated as an instruction the user can carry out.
    # `decision` is the machine-readable form; this is the executable one.
    action: str = ""
    # The answer as a zero-order expansion: trunk, corrections, overturns, vetoes.
    perturbation: list[PerturbationTerm] = field(default_factory=list)

    @property
    def zero_order(self) -> Optional[PerturbationTerm]:
        """The trunk — the answer the dominant terms alone give."""
        return next((t for t in self.perturbation if t.order == ORDER_ZERO), None)

    @property
    def corrections(self) -> list[PerturbationTerm]:
        """一阶修正. Refine the trunk; by construction cannot overturn it."""
        return [t for t in self.perturbation if t.order == ORDER_FIRST]

    @property
    def overturns(self) -> list[PerturbationTerm]:
        """翻盘项. Not corrections — each is a different zero-order model. These are
        what the flip test (翻盘检验) asks about: what could reverse the conclusion."""
        return [t for t in self.perturbation if t.order == ORDER_OVERTURN]

    @property
    def dropped(self) -> list[PerturbationTerm]:
        """舍去项. Terms 主导平衡 threw away: no causal control over the outcome, so
        they were removed before any preference was elicited."""
        return [t for t in self.perturbation if t.order == ORDER_DROPPED]

    @property
    def hard_constraints(self) -> list[PerturbationTerm]:
        """硬约束. Conditions under which no zero-order answer exists at all."""
        return [t for t in self.perturbation if t.order == ORDER_HARD]

    @property
    def assumptions_to_confirm(self) -> list[SensitivityEntry]:
        """The elicited assumptions that would change the decision if they turn
        out to be wrong. These are factual risks, not analytical ones: no further
        computation resolves them, only checking the world."""
        return [s for s in self.sensitivity if s.decision_changed]

    @property
    def analysis_is_complete(self) -> bool:
        """True when no further analysis can improve this answer.

        The contract was complete (dispatch would have raised otherwise), the
        assumption set is covered by the corpus, and every validation invariant
        passed. What remains is not more thinking — it is confirming the facts
        listed in `assumptions_to_confirm` and then acting.
        """
        return self.audit.passed

    @property
    def execution_note(self) -> str:
        """Plain-language answer to 'may I stop analyzing and start executing?'"""
        if not self.analysis_is_complete:
            failed = ", ".join(f.invariant_id for f in self.audit.failures)
            return (
                f"DO NOT EXECUTE. The audit failed ({failed}). This decision is not "
                "actionable; re-elicit the implicated fields and re-run."
            )
        pending = self.assumptions_to_confirm
        if not pending:
            return (
                "EXECUTE. The analysis is complete and no elicited assumption, if "
                "changed, alters this decision. Further deliberation cannot improve it."
            )
        names = ", ".join(sorted({s.assumption for s in pending}))
        return (
            "EXECUTE once you have confirmed: " + names + ". "
            "The analysis itself is complete — these are facts to check, not further "
            "calculations to run. If they hold as elicited, stop analyzing and act."
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["analysis_is_complete"] = self.analysis_is_complete
        d["execution_note"] = self.execution_note
        return d

    def to_markdown(self) -> str:
        lines = [
            f"## Decision",
        ]
        if self.action:
            lines.append(f"**{self.action}**")
            lines.append("")
            lines.append(f"Machine-readable: `{self.decision}`")
        else:
            lines.append(f"**{self.decision}**")
        lines += [
            "",
            f"## Formula",
            f"- Name: {self.formula_name}",
            f"- Citation: `{self.citation}`",
            f"- LaTeX: `{self.formula_latex}`",
            "",
            f"## Numeric",
        ]
        for k, v in self.numeric.items():
            lines.append(f"- {k}: {v}")
        lines += ["", "## Assumptions"]
        for k, v in self.assumptions.items():
            lines.append(f"- {k}: {v}")
        lines += ["", "## Sensitivity"]
        for s in self.sensitivity:
            lines.append(
                f"- {s.assumption} ({s.perturbation}): "
                f"{'CHANGED' if s.decision_changed else 'stable'} → {s.new_decision} [{s.fragility}]"
            )
        lines += ["", "## Audit"]
        status = "PASS" if self.audit.passed else "FAIL"
        lines.append(f"Status: **{status}**")
        for r in self.audit.results:
            mark = "✓" if r.passed else "✗"
            lines.append(f"- [{mark}] {r.invariant_id} {r.name}: {r.message}")

        if self.perturbation:
            lines += ["", "## Zero-order expansion (零阶展开)", ""]
            lines.append("| Order | Term | Value | Δ vs trunk | Citation |")
            lines.append("|---|---|---|---|---|")
            for t in self.perturbation:
                shift = "—" if t.relative_shift is None else f"{t.relative_shift:+.0%}"
                lines.append(
                    f"| {t.gloss} | {t.label} | {t.value} | {shift} | `{t.citation}` |"
                )
            notes = [t for t in self.perturbation if t.note]
            if notes:
                lines.append("")
                for t in notes:
                    lines.append(f"- **{t.label}** — {t.note}")

        lines += ["", "## Execute", self.execution_note]
        pending = self.assumptions_to_confirm
        if self.analysis_is_complete and pending:
            for s in pending:
                lines.append(
                    f"- **{s.assumption}** — if {s.perturbation}, the decision "
                    f"becomes {s.new_decision} [{s.fragility}]"
                )
        return "\n".join(lines)
