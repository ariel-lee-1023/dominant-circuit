# main.py
from src.dominant_circuit.engine import DominantCircuitEngine

def main():
    print("Dominant-Circuit Zero-Order Engine Initialized.")
    print("Nature cannot be fooled.\n")
    
    engine = DominantCircuitEngine()
    
    # Example scenario
    query = input("State your decision problem: ")
    
    try:
        engine.run_socratic_loop(query)
        result = engine.dispatch()
        
        print("\n--- FINAL OUTPUT ---")
        for key, value in result.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
            
    except ValueError as e:
        print(f"\nAUDIT FAILURE: {e}")
        print("Please restart and provide physically valid constraints.")

if __name__ == "__main__":
    main()
