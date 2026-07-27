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

    def to_dict(self) -> dict:
        return asdict(self)

    def to_markdown(self) -> str:
        lines = [
            f"## Decision",
            f"**{self.decision}**",
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
        return "\n".join(lines)
