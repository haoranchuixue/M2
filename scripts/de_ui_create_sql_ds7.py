"""Create SQL dataset - find SQL mode icon, look at table list layout."""
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
    
    save_payloads = []
    def handle_request(request):
        if 'datasetTree/save' in request.url:
            save_payloads.append(request.post_data)
    page.on('request', handle_request)
    
    page.goto(f'{base}/', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_load_state('networkidle', timeout=30000)
    page.wait_for_selector('input', timeout=10000)
    inputs = page.query_selector_all('input')
    inputs[0].fill('admin')
    inputs[1].fill('DataEase@123456')
    page.query_selector('button').click()
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)
    
    # Go directly to dataset form with PID
    page.goto(f'{base}/#/dataset-form?pid=1236043392912330752', timeout=30000, wait_until='domcontentloaded')
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=15000)
    print(f"URL: {page.url}")
    
    # Select starrocks datasource
    ds_select = page.query_selector('.ed-select:has-text("请选择数据源")')
    if ds_select:
        ds_select.click()
        time.sleep(2)
        sr_option = page.query_selector('.ed-select-dropdown__item:has-text("starrocks")')
        if sr_option:
            sr_option.click()
            time.sleep(3)
            page.wait_for_load_state('networkidle', timeout=10000)
            print("Selected starrocks datasource")
    
    # Get the table-list HTML to find the SQL toggle
    table_list_html = page.evaluate("""() => {
        const tl = document.querySelector('.table-list');
        return tl ? tl.innerHTML.substring(0, 5000) : 'no table-list';
    }""")
    print(f"\nTable-list HTML:\n{table_list_html[:3000]}")
    
    # Look for text like "SQL" or any hidden buttons in the table-list header
    # Also look for tabs at the top like "数据表" and "SQL"
    tab_els = page.evaluate("""() => {
        // Check for radio-group, tabs, or any type selector near the table-list
        const tabGroups = document.querySelectorAll('.ed-tabs, .ed-radio-group, [class*="tab-header"]');
        return Array.from(tabGroups).map(g => ({
            class: g.className?.substring(0, 100) || '',
            text: g.textContent?.trim()?.substring(0, 200) || '',
            visible: g.offsetParent !== null
        }));
    }""")
    print(f"\nTab groups: {len(tab_els)}")
    for tg in tab_els:
        if tg['visible']:
            print(f"  class='{tg['class'][:80]}' text='{tg['text']}'")
    
    # Maybe there's a header with "数据表" and a number, and an icon to switch to SQL
    header = page.query_selector('.table-list .header, .table-list [class*="header"]')
    if header:
        header_html = header.evaluate("el => el.outerHTML.substring(0, 1000)")
        print(f"\nTable-list header HTML:\n{header_html}")
    
    # Check for all visible clickable icons in the table-list area
    clickable = page.evaluate("""() => {
        const tl = document.querySelector('.table-list');
        if (!tl) return [];
        const els = tl.querySelectorAll('i, svg, span, div');
        return Array.from(els).filter(e => {
            return e.offsetParent !== null && 
                   (e.tagName === 'I' || e.tagName === 'SVG' || e.style.cursor === 'pointer' || 
                    e.getAttribute('role') === 'button');
        }).map(e => ({
            tag: e.tagName,
            class: (e.className || '').toString().substring(0, 100),
            text: (e.textContent || '').trim().substring(0, 30),
            rect: e.getBoundingClientRect()
        })).slice(0, 30);
    }""")
    print(f"\nClickable elements in table-list: {len(clickable)}")
    for ce in clickable[:15]:
        r = ce['rect']
        print(f"  <{ce['tag']}> class='{str(ce['class'])[:60]}' text='{ce['text']}' at ({r['x']:.0f},{r['y']:.0f})")
    
    page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds7_form.png')
    
    browser.close()
    print("\nDone!")
