
from playwright.sync_api import sync_playwright
import time

def verify_task_graph():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Visit the local dev server
            page.goto("http://localhost:5173")

            # Wait for the page to load
            time.sleep(2)

            # Check if the TaskGraph container is visible
            # The container has class "task-graph-container"
            graph_container = page.locator(".task-graph-container")
            graph_container.wait_for(state="visible", timeout=5000)

            # Since we have no simulation state, it should show "Waiting for Simulation..."
            waiting_text = page.get_by_text("Waiting for Simulation...")
            if waiting_text.is_visible():
                print("Verified: 'Waiting for Simulation...' message is visible.")
            else:
                print("Warning: 'Waiting for Simulation...' message not found.")

            # Take a screenshot
            page.screenshot(path="verification/task_graph_verified.png")
            print("Screenshot saved to verification/task_graph_verified.png")

        except Exception as e:
            print(f"Verification failed: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_task_graph()
