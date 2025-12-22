
from playwright.sync_api import sync_playwright

def verify_kpi(page):
    # Navigate to the app (assuming dev server runs on 5173)
    page.goto('http://localhost:5173')

    # Wait for the dashboard to load
    page.wait_for_selector('.kpi-dashboard')

    # Check for new accessibility roles
    region = page.get_by_role('region', name='Key Performance Indicators')
    assert region.is_visible()

    # Check for tooltip/title on an item
    iter_item = page.locator('.kpi-item[title="Current Iteration Count"]')
    assert iter_item.is_visible()

    # Take screenshot of the KPI dashboard area
    # KPI dashboard is an overlay, so we might screenshot the whole page
    page.screenshot(path='verification/kpi_dashboard.png')

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    try:
        verify_kpi(page)
        print('Verification script finished successfully.')
    except Exception as e:
        print(f'Verification failed: {e}')
    finally:
        browser.close()
