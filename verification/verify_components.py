from playwright.sync_api import sync_playwright

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            print("Navigating to http://localhost:5173")
            page.goto("http://localhost:5173")

            # Wait for the Control Tower header to appear
            print("Waiting for Control Tower header")
            page.wait_for_selector("text=Project Prometheus: Control Tower")

            # Check for KPIDashboard components
            print("Checking KPIDashboard")
            page.wait_for_selector("text=Iteration")
            page.wait_for_selector("text=Active Strategies")

            # Check for ThinkingPanel
            print("Checking ThinkingPanel")
            page.wait_for_selector("text=Thinking")

            # Check for TaskGraph
            print("Checking TaskGraph")
            page.wait_for_selector("text=Strategy Evolution Graph")

            # Check for ChatPanel
            print("Checking ChatPanel")
            page.wait_for_selector("text=Send")

            # Take a screenshot to verify everything renders correctly
            print("Taking screenshot")
            page.screenshot(path="verification/frontend_verified.png")
            print("Verification complete")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_frontend()
