"""Create SQL dataset - navigate form, select SQL mode, enter query."""
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
    
    # Track dataset save API
    save_payloads = []
    def handle_request(request):
        if 'datasetTree/save' in request.url:
            save_payloads.append(request.post_data)
    page.on('request', handle_request)
    
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
    
    # Hover on DSP Report and click create menu
    dsp_el = page.query_selector('span.label-tooltip:has-text("DSP Report")')
    if not dsp_el:
        dsp_el = page.query_selector('span:has-text("DSP Report")')
    dsp_el.hover()
    time.sleep(1)
    hover_icons = page.query_selector_all('.ed-icon.hover-icon')
    hover_icons[0].click()
    time.sleep(2)
    
    new_ds = page.query_selector('.ed-dropdown-menu__item:has-text("新建数据集")')
    if not new_ds:
        new_ds = page.query_selector('text="新建数据集"')
    new_ds.click()
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    print(f"Dataset form URL: {page.url}")
    
    # Step 1: Select the data source (starrocks)
    # Look for datasource selection dropdown
    ds_select = page.query_selector('.ed-select:has-text("请选择数据源"), .ed-select__wrapper, [class*="select"]:has-text("请选择数据源")')
    if ds_select:
        print("Found datasource select, clicking...")
        ds_select.click()
        time.sleep(2)
        
        # Look for starrocks option in dropdown
        sr_option = page.query_selector('.ed-select-dropdown__item:has-text("starrocks"), .ed-option:has-text("starrocks")')
        if sr_option:
            print("Found starrocks option!")
            sr_option.click()
            time.sleep(2)
    else:
        # Try clicking on "请选择数据源" text directly
        placeholder = page.query_selector('text="请选择数据源"')
        if placeholder:
            print("Clicking datasource placeholder...")
            placeholder.click()
            time.sleep(2)
            page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds6_ds_select.png')
            
            # Look for dropdown options
            options = page.evaluate("""() => {
                const items = document.querySelectorAll('.ed-select-dropdown__item, .ed-option, [class*="select-dropdown"] [class*="item"]');
                return Array.from(items).filter(i => i.offsetParent !== null).map(i => ({
                    text: i.textContent?.trim() || ''
                }));
            }""")
            print(f"Dropdown options: {len(options)}")
            for opt in options:
                print(f"  '{opt['text']}'")
            
            # Click starrocks option
            sr = page.query_selector('[class*="select-dropdown"] [class*="item"]:has-text("starrocks")')
            if not sr:
                sr = page.query_selector('text="starrocks"')
            if sr:
                print("Clicking starrocks...")
                sr.click()
                time.sleep(3)
    
    page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds6_ds_selected.png')
    page.wait_for_load_state('networkidle', timeout=10000)
    
    # Step 2: Find SQL toggle/tab
    # Look for a SQL toggle, tab, or icon
    sql_elements = page.evaluate("""() => {
        const all = document.querySelectorAll('*');
        let results = [];
        for (let el of all) {
            let text = el.textContent?.trim() || '';
            let cls = el.className || '';
            if (typeof cls === 'string' && (cls.includes('sql') || cls.includes('SQL'))) {
                results.push({tag: el.tagName, class: cls.substring(0, 100), text: text.substring(0, 50), visible: el.offsetParent !== null});
            }
            if (text === 'SQL' && el.children.length === 0) {
                results.push({tag: el.tagName, class: (typeof cls === 'string' ? cls : '').substring(0, 100), text: text, visible: el.offsetParent !== null});
            }
        }
        return results;
    }""")
    print(f"\nSQL-related elements: {len(sql_elements)}")
    for el in sql_elements:
        print(f"  <{el['tag']}> class='{el.get('class', '')[:80]}' visible={el['visible']} text='{el['text']}'")
    
    # Look for a toggle or switch near the table list
    toggles = page.query_selector_all('[class*="toggle"], [class*="switch"], [class*="segment"]')
    print(f"\nToggles/switches: {len(toggles)}")
    for i, t in enumerate(toggles):
        text = t.text_content() or ''
        cls = t.get_attribute('class') or ''
        vis = t.is_visible()
        if vis:
            print(f"  [{i}] '{text.strip()[:50]}' class='{cls[:80]}'")
    
    # Check for icon buttons in the table list area
    table_area = page.query_selector('.table-list')
    if table_area:
        icons_in_table = table_area.query_selector_all('[class*="icon"]')
        print(f"\nIcons in table-list area: {len(icons_in_table)}")
        for i, ic in enumerate(icons_in_table):
            cls = ic.get_attribute('class') or ''
            vis = ic.is_visible()
            title = ic.get_attribute('title') or ''
            if vis:
                print(f"  [{i}] class='{cls[:80]}' title='{title}'")
    
    page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds6_final.png')
    
    browser.close()
    print("\nDone!")
