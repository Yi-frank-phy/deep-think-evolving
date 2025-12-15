
from playwright.sync_api import sync_playwright

def verify_copy_button():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to the app (assuming default Vite port)
            page.goto("http://localhost:5173")

            # Wait for messages to load
            page.wait_for_selector(".message", timeout=10000)

            # Hover over a message to show the button
            # We target the last message as it's most likely visible without scrolling
            messages = page.locator(".message")
            count = messages.count()
            if count > 0:
                last_message = messages.nth(count - 1)
                last_message.hover()

                # Check for button visibility
                copy_button = last_message.locator("button[aria-label='Copy message text']")
                # It might take a moment for opacity transition, but Playwright might consider it visible if it's in the DOM and not display:none
                # We can wait for it
                copy_button.wait_for(state="visible", timeout=2000)

                # Take screenshot
                page.screenshot(path="verification/copy_button_hover.png")
                print("Screenshot taken: verification/copy_button_hover.png")

                # Click it to test interaction
                copy_button.click()

                # Check if icon changed to checkmark (aria-label changes to "Copied")
                # wait for re-render
                page.wait_for_selector("button[aria-label='Copied']", timeout=2000)

                # Take another screenshot
                page.screenshot(path="verification/copy_button_clicked.png")
                print("Screenshot taken: verification/copy_button_clicked.png")

            else:
                print("No messages found")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_copy_button()
