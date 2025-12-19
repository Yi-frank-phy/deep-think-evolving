
import asyncio
from playwright.async_api import async_playwright
import sys

async def verify():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            print("Navigating to http://localhost:4173...")
            response = await page.goto("http://localhost:4173", timeout=10000)
            if not response:
                print("Failed to get response")
                sys.exit(1)

            print(f"Status: {response.status}")

            # Wait for the layout to appear
            print("Waiting for .gemini-layout...")
            await page.wait_for_selector(".gemini-layout", timeout=10000)

            # Check for sidebar and main
            sidebar = await page.query_selector(".gemini-sidebar")
            main = await page.query_selector(".gemini-main")

            if sidebar and main:
                print("SUCCESS: Gemini layout elements found.")
            else:
                print("FAILURE: Sidebar or Main missing.")
                sys.exit(1)

            await page.screenshot(path="verification/layout_verified.png")
            print("Screenshot saved to verification/layout_verified.png")

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(verify())
