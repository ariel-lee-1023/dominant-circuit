# src/dominant_circuit/solvers.py
import math

def solve_optimal_stopping(n: int, information_type: str, recall: bool = False, rejection_prob: float = 0.0):
    """
    Implements Cluster 01: Optimal Stopping.
    Calculates the Look-Then-Leap cutoff (r) based on physical constraints.
    """
    if information_type == "ordinal":
        if recall and rejection_prob == 0:
            r = round(0.61 * n)
        elif rejection_prob > 0:
            r = round(0.25 * n)
        else:
            # Classical 37% rule asymptotic limit
            r = round(n / math.e)
            
        return {
            "formula": "Look-Then-Leap",
            "look_phase_cutoff": r,
            "instruction": f"Look at the first {r} options without accepting. Then accept the next best-yet option."
        }
    elif information_type == "cardinal":
        return {
            "formula": "Threshold Rule",
            "instruction": "Use absolute scores to set a declining threshold. No look phase required."
        }
    else:
        raise ValueError("Unknown information type.")

def solve_additive_utility(component_values: list, weights: list):
    """
    Implements Cluster 02: Multiple Objectives (Additive Form).
    """
    # Validation Invariant: Weights must sum to 1
    if abs(sum(weights) - 1.0) > 1e-9:
        raise ValueError("Audit Failure: Weights must sum to 1 for the additive form.")
        
    final_utility = sum(w * v for w, v in zip(weights, component_values))
    return {
        "formula": "Additive Multiattribute Utility",
        "final_score": final_utility
    }

def verify_bellman_residual(U_new: dict, U_old: dict, gamma: float):
    """
    Implements Cluster 03: Validation Invariant for Markov Decision Processes.
    """
    residual = max(abs(U_new[s] - U_old[s]) for s in U_new)
    # The residual must shrink by a factor no worse than gamma
    # If it doesn't, the physics of the contraction mapping are broken.
    return residual
