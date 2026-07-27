"""Demonstration CLI — non-blocking. Builds fully-specified contracts in code."""

from __future__ import annotations

from dominant_circuit import (
    dispatch, InputContract, Job, Horizon, Information, Payoff,
)


def demo_classical_secretary(n: int = 100) -> None:
    contract = InputContract(
        job=Job.STOPPING,
        horizon=Horizon.FIXED_KNOWN,
        n=n,
        information=Information.ORDINAL,
        payoff=Payoff.BEST_OR_NOTHING,
        payoff_diverges=False,
        recall_allowed=False,
        rejection_prob=0.0,
        exact_finite_n=True,
    )
    report = dispatch(Job.STOPPING, contract)
    print(report.to_markdown())
    print()


def demo_cost_of_search() -> None:
    contract = InputContract(
        job=Job.STOPPING,
        horizon=Horizon.UNBOUNDED_STREAM,
        payoff=Payoff.COST_OF_SEARCH,
        payoff_diverges=False,
        search_cost=0.02,
        information=Information.CARDINAL,
    )
    report = dispatch(Job.STOPPING, contract)
    print(report.to_markdown())
    print()


def demo_diverging_blocked() -> None:
    contract = InputContract(
        job=Job.STOPPING,
        horizon=Horizon.FIXED_KNOWN,
        n=10,
        information=Information.ORDINAL,
        payoff=Payoff.BEST_OR_NOTHING,
        payoff_diverges=True,
    )
    try:
        dispatch(Job.STOPPING, contract)
    except Exception as e:
        print(f"Correctly blocked: {type(e).__name__}: {e}")
        print(f"  remedy: {getattr(e, 'remedy', '')}")
        print()


def main() -> None:
    print("Dominant-Circuit Zero-Order Engine (non-interactive demo)\n")
    print("=" * 60)
    print("Demo 1: Classical secretary n=100 (exact finite-n)")
    print("=" * 60)
    demo_classical_secretary(100)

    print("=" * 60)
    print("Demo 2: Cost-of-search (c=0.02)")
    print("=" * 60)
    demo_cost_of_search()

    print("=" * 60)
    print("Demo 3: Diverging payoff must be blocked")
    print("=" * 60)
    demo_diverging_blocked()


if __name__ == "__main__":
    main()
