"""Demonstration CLI — non-blocking. Builds fully-specified contracts in code."""

from __future__ import annotations

from dominant_circuit import (
    dispatch, InputContract, Job, Horizon, Information, Payoff,
    AttributeRange, IndependenceNotVerified, next_question, missing_fields,
    independence_questions, record_independence,
)


def demo_elicitation_loop() -> None:
    """Stage 1: the library asks nothing; it reports what is still missing.

    A host drives this loop against a real user. Here the 'answers' are scripted
    so the demo stays non-interactive — but note that nothing is ever defaulted:
    each field is set only because an answer was supplied for it.
    """
    scripted = {
        "horizon": Horizon.FIXED_KNOWN,
        "payoff": Payoff.BEST_OR_NOTHING,
        "payoff_diverges": False,
        "information": Information.ORDINAL,
        "n": 50,
    }
    contract = InputContract(job=Job.STOPPING)
    while (question := next_question(contract)) is not None:
        field = missing_fields(contract)[0]
        print(f"  ASK  ({field}): {question}")
        print(f"  USER: {scripted[field]}")
        setattr(contract, field, scripted[field])
    print("\n  Contract complete. Nothing was inferred.\n")
    print(dispatch(Job.STOPPING, contract).to_markdown())
    print()


def demo_independence_protocol() -> None:
    """Stage 2: the flip-test checkpoint, driven the way a host would."""
    contract = InputContract(
        job=Job.MULTIOBJECTIVE,
        attributes=[
            AttributeRange("salary", 40, 100),
            AttributeRange("commute", 60, 10, monotonic_increasing=False),
        ],
        scaling_constants={"salary": 0.65, "commute": 0.35},
        independence_assumptions=[],
        alternatives=[
            {"name": "Offer A", "salary": 80, "commute": 20},
            {"name": "Offer B", "salary": 60, "commute": 15},
            {"name": "Offer C", "salary": 55, "commute": 45},
        ],
    )
    try:
        dispatch(Job.MULTIOBJECTIVE, contract)
    except IndependenceNotVerified as e:
        print(f"  Blocked: {e}")
        print(f"  Remedy:  {e.remedy}\n")

    for subset, complement, question in independence_questions(contract):
        print(f"  ASK  ({'{'}{', '.join(sorted(subset))}{'}'}): {question}")
        print("  USER: yes")
        contract.independence_assumptions.append(
            record_independence(subset, complement, contract.independence_kind,
                                verified=True, evidence="scripted demo answer")
        )

    report = dispatch(Job.MULTIOBJECTIVE, contract)
    print(f"\n  Gate now open. {report.action}")
    print(f"  {report.execution_note}\n")


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

    print("=" * 60)
    print("Demo 4: Stage 1 — elicitation loop (host asks, library never does)")
    print("=" * 60)
    demo_elicitation_loop()

    print("=" * 60)
    print("Demo 5: Stage 2 — independence protocol (the flip-test checkpoint)")
    print("=" * 60)
    demo_independence_protocol()


if __name__ == "__main__":
    main()
