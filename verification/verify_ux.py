from playwright.sync_api import sync_playwright

def verify_ux():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            print("Navigating to http://localhost:5173/")
            page.goto("http://localhost:5173/")

            # Wait for the dashboard to load
            page.wait_for_selector("#dashboard", timeout=10000)
            print("Dashboard loaded")

            # Verify Control Tower presence
            control_tower = page.locator(".control-tower")

            # Verify Voice Button (Mic or Square)
            # We expect Mic icon (svg with lucid-react class usually doesn't have a specific class but we can check if svg is there)
            # Or better, check the aria-label we added
            voice_btn = page.locator('button[aria-label="Record voice problem"]')
            if voice_btn.count() > 0:
                print("✅ Voice button with aria-label found")
            else:
                print("❌ Voice button NOT found")

            # Verify Start Mission button has an icon
            start_btn = page.locator('button.primary', has_text="Start Mission")
            if start_btn.locator('svg').count() > 0:
                print("✅ Start Mission button has icon")
            else:
                print("❌ Start Mission button missing icon")

            # Verify Input aria-label
            input_el = page.locator('input[aria-label="Problem statement"]')
            if input_el.count() > 0:
                print("✅ Input with aria-label found")
            else:
                print("❌ Input missing aria-label")

            # Take a screenshot of the control tower area
            control_tower.screenshot(path="verification/control_tower_ux.png")
            print("Screenshot saved to verification/control_tower_ux.png")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_ux()
