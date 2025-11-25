import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Importing main...")
    import main
    print("Imported main successfully.")
    
    print("Importing run_pipeline...")
    from main import run_pipeline
    print("Imported run_pipeline successfully.")
    
    print("Importing src.logging_utils...")
    import src.logging_utils
    print("Imported src.logging_utils successfully.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
