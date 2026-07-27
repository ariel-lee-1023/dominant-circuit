# src/dominant_circuit/engine.py
from .solvers import solve_optimal_stopping, solve_additive_utility

class DominantCircuitEngine:
    def __init__(self):
        self.contract = {}
        self.job = None

    def run_socratic_loop(self, user_query: str):
        """
        The front-end state machine. Forces the user to fill the Input Contract.
        (In production, connect this to the LLM to parse human language).
        """
        print(f"Analyzing user query: '{user_query}'")
        
        # Simple routing logic
        if "stop" in user_query or "looking" in user_query:
            self.job = "stopping"
            self.contract['n'] = int(input("How many total options do you have (N)? "))
            self.contract['information_type'] = input("Can you rank them (ordinal) or score them absolutely (cardinal)? ")
            self.contract['infinite_payoff'] = False # Ask user if rewards diverge
            
        elif "tradeoff" in user_query or "objectives" in user_query:
            self.job = "multiobjective"
            self.contract['independence_verified'] = input("Did the user pass the flip test for utility independence? (yes/no) ").strip().lower() == "yes"
            self.contract['weights'] = [float(x) for x in input("Enter weights separated by space (must sum to 1): ").split()]
            self.contract['values'] = [float(x) for x in input("Enter normalized component values separated by space: ").split()]

    def verify_preconditions(self):
        """Blocks computation if physical or mathematical laws are violated."""
        if self.job == "stopping" and self.contract.get('infinite_payoff'):
            raise ValueError("Hard Precondition Failed: Expected payoff diverges. No stopping rule exists.")
            
        if self.job == "multiobjective" and not self.contract.get('independence_verified'):
            raise ValueError("Hard Precondition Failed: Mutual utility independence not verified. Cannot use additive formula.")

    def dispatch(self):
        """Routes valid parameters to the mathematical solvers."""
        self.verify_preconditions()
        
        if self.job == "stopping":
            return solve_optimal_stopping(
                n=self.contract['n'],
                information_type=self.contract['information_type']
            )
        elif self.job == "multiobjective":
            return solve_additive_utility(
                component_values=self.contract['values'],
                weights=self.contract['weights']
            )
        else:
            raise NotImplementedError("Job type not yet implemented.")
