
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Ensure src is in path
sys.path.append(os.getcwd())

def test_graph_compilation():
    with patch("src.agents.architect.generate_strategic_blueprint") as mock_gen:
        # Mock dependencies to avoid import errors if some libs are missing deep down
        # (Though we expect them to be present)
        
        try:
            from src.core.graph_builder import build_deep_think_graph
            app = build_deep_think_graph()
            assert app is not None
            print("[PASS] Graph compiled successfully.")
            
            # Use internal graph method to check nodes if available, 
            # but usually just compiling without error is a good smoke test.
            
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
        except Exception as e:
            pytest.fail(f"Graph build failed: {e}")

if __name__ == "__main__":
    # Simple run
    test_graph_compilation()
