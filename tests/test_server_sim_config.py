
import sys
import os
from fastapi.testclient import TestClient
from server import app

# Ensure root is in path
sys.path.append(os.getcwd())

def test_simulation_with_config():
    print("\n--- Testing Simulation Endpoints with Config ---")
    client = TestClient(app)
    
    with client.websocket_connect("/ws/simulation") as websocket:
        print("[Client] Connected to WS")
        
        # Start Simulation with Config
        payload = {
            "problem": "Test Problem",
            "config": {
                "t_max": 5.0,
                "c_explore": 2.0,
                "beam_width": 5
            }
        }
        
        response = client.post("/api/simulation/start", json=payload)
        print(f"[Client] Start Response: {response.json()}")
        assert response.status_code == 200
        assert response.json()["status"] == "started"
        
        # Receive "started" status
        data = websocket.receive_json()
        print(f"[Client] Received WS: {data}")
        assert data["type"] == "status"
        
        # Stop Simulation
        response = client.get("/api/simulation/stop")
        print(f"[Client] Stop Response: {response.json()}")
        assert response.status_code == 200

if __name__ == "__main__":
    test_simulation_with_config()
