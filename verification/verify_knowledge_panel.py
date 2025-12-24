
from playwright.sync_api import sync_playwright
import time

def verify_knowledge_panel():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Navigate to the app
            page.goto("http://localhost:5173")

            # Wait for the app to load
            page.wait_for_selector(".gemini-layout", timeout=10000)

            # The KnowledgePanel is in the bottom right, initially empty.
            # We want to verify the "Knowledge Base Empty" state.

            # Wait for the KnowledgePanel header to appear
            page.wait_for_selector("h2:has-text('Knowledge Base')")

            # Check for the empty state text
            empty_state_locator = page.get_by_text("Knowledge Base Empty")

            # Take a screenshot of the entire page to see context
            page.screenshot(path="verification/full_page.png")

            # Take a screenshot of just the Knowledge Panel if possible
            # We can use the id="knowledge-panel"
            knowledge_panel = page.locator("#knowledge-panel")
            if knowledge_panel.count() > 0:
                knowledge_panel.screenshot(path="verification/knowledge_panel_empty.png")
                print("Screenshot taken: verification/knowledge_panel_empty.png")
            else:
                print("Could not find #knowledge-panel for screenshot")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_knowledge_panel()
