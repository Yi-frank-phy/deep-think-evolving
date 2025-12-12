from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:5173")

        # Click Config button to open panel
        page.get_by_role("button", name="Config").click()

        # Wait for the slider to be visible
        # We look for the label "Max Temp (T_max)"
        # Note: In the code we changed the label structure, so we might need to be specific.
        # The label text should contain "Max Temp (T_max)"

        # Wait for config panel animation if any
        page.wait_for_timeout(1000)

        # Take screenshot of the config panel area
        page.screenshot(path="verification/tmax_slider.png")

        browser.close()

if __name__ == "__main__":
    run()
