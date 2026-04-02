"""Create SQL-type dataset via DataEase UI - full flow."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
sql_query = "SELECT * FROM dsp_report WHERE create_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # Track API for dataset save
    save_requests = []
    save_responses = []
    def handle_request(request):
        if 'datasetTree' in request.url:
            save_requests.append({'url': request.url, 'method': request.method, 'body': request.post_data})
    def handle_response(response):
        if 'datasetTree' in response.url and response.status == 200:
            try:
                save_responses.append({'url': response.url, 'body': response.json()})
            except:
                pass
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    # Login
    page.goto(f'{base}/', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_load_state('networkidle', timeout=30000)
    page.wait_for_selector('input', timeout=10000)
    inputs = page.query_selector_all('input')
    inputs[0].fill('admin')
    inputs[1].fill('DataEase@123456')
    page.query_selector('button').click()
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)
    print("Logged in")
    
    # Go to dataset page
    page.goto(f'{base}/#/data/dataset', timeout=30000, wait_until='domcontentloaded')
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    # Hover on DSP Report group and click the first hover icon (create menu)
    dsp_el = page.query_selector('span.label-tooltip:has-text("DSP Report")')
    if not dsp_el:
        dsp_el = page.query_selector('span:has-text("DSP Report")')
    
    print("Step 1: Opening create menu...")
    dsp_el.hover()
    time.sleep(1)
    hover_icons = page.query_selector_all('.ed-icon.hover-icon')
    hover_icons[0].click()
    time.sleep(2)
    
    # Click "新建数据集"
    new_ds = page.query_selector('.ed-dropdown-menu__item:has-text("新建数据集")')
    if not new_ds:
        new_ds = page.query_selector('text="新建数据集"')
    print("Step 2: Clicking '新建数据集'...")
    new_ds.click()
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds5_create_dialog.png')
    print(f"URL after create: {page.url}")
    
    # Check what appeared - could be a dialog or a new page
    # Look for dialog or form elements
    dialogs = page.query_selector_all('.ed-dialog, .el-dialog, [class*="dialog"]')
    print(f"Dialogs: {len(dialogs)}")
    
    # Check visible text for dataset type selection
    visible_text = page.evaluate("() => document.body.innerText")
    # Look for SQL-related options
    for keyword in ['SQL', 'sql', '数据库表', '数据源']:
        if keyword in visible_text:
            print(f"  Found keyword: '{keyword}'")
    
    # Look for tabs or selection options for dataset type
    tabs = page.query_selector_all('[class*="tab"], [role="tab"]')
    print(f"\nTabs: {len(tabs)}")
    for i, tab in enumerate(tabs):
        text = tab.text_content() or ''
        vis = tab.is_visible()
        if vis:
            print(f"  [{i}] '{text.strip()}'")
    
    # Look for radio buttons or options
    radios = page.query_selector_all('[class*="radio"], [type="radio"]')
    print(f"\nRadios: {len(radios)}")
    
    # Check for SQL tab or SQL option
    sql_tab = page.query_selector('[class*="tab"]:has-text("SQL")')
    if sql_tab:
        print("\nFound SQL tab, clicking...")
        sql_tab.click()
        time.sleep(2)
        page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds5_sql_tab.png')
    
    # Look at the current page structure more carefully
    form_html = page.evaluate("""() => {
        const main = document.querySelector('.main-area, .content-area, [class*="main"], [class*="content"]');
        if (main) return main.outerHTML.substring(0, 3000);
        return document.body.innerHTML.substring(0, 5000);
    }""")
    print(f"\nForm/Main area HTML:\n{form_html[:2000]}")
    
    browser.close()
    print("\nDone!")
