"""Create SQL-type dataset via DataEase UI - explore the hover menu on DSP Report group."""
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
    
    # Track API calls for dataset creation
    api_calls = []
    def handle_request(request):
        if 'datasetTree/save' in request.url:
            api_calls.append({
                'url': request.url,
                'method': request.method,
                'body': request.post_data
            })
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
    
    page.goto(f'{base}/#/data/dataset', timeout=30000, wait_until='domcontentloaded')
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    # Find and hover over DSP Report group
    dsp_el = page.query_selector('span.label-tooltip:has-text("DSP Report")')
    if not dsp_el:
        dsp_el = page.query_selector('span:has-text("DSP Report")')
    
    if dsp_el:
        print("Hovering on DSP Report group...")
        dsp_el.hover()
        time.sleep(1)
        
        # Click the first hover icon (likely "add" or "create")
        hover_icons = page.query_selector_all('.ed-icon.hover-icon')
        print(f"Hover icons found: {len(hover_icons)}")
        
        if hover_icons:
            # Click the first hover icon
            print("Clicking first hover icon...")
            hover_icons[0].click()
            time.sleep(2)
            page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds4_first_icon.png')
            
            # Check if a menu appeared
            menu_items = page.query_selector_all('.ed-dropdown-menu__item:visible, .el-dropdown-menu__item:visible')
            if not menu_items:
                # Try broader search
                all_menus = page.evaluate("""() => {
                    const items = document.querySelectorAll('.ed-dropdown-menu__item, .el-dropdown-menu__item, [class*="dropdown-menu"] [class*="item"]');
                    return Array.from(items).map(i => ({
                        text: i.textContent?.trim() || '',
                        visible: i.offsetParent !== null
                    }));
                }""")
                print(f"All dropdown items: {len(all_menus)}")
                for mi in all_menus:
                    print(f"  '{mi['text']}' visible={mi['visible']}")
            else:
                print(f"Menu items: {len(menu_items)}")
                for mi in menu_items:
                    text = mi.text_content() or ''
                    print(f"  '{text.strip()}'")
        
        # Also try the second hover icon (the "..." dropdown)
        if len(hover_icons) > 1:
            print("\nHovering again and clicking second hover icon...")
            dsp_el.hover()
            time.sleep(1)
            hover_icons = page.query_selector_all('.ed-icon.hover-icon')
            if len(hover_icons) > 1:
                hover_icons[1].click()
                time.sleep(2)
                page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds4_second_icon.png')
                
                # Check menu
                all_menus = page.evaluate("""() => {
                    const items = document.querySelectorAll('.ed-dropdown-menu__item, .el-dropdown-menu__item, [class*="dropdown-menu"] [class*="item"]');
                    return Array.from(items).filter(i => i.offsetParent !== null).map(i => ({
                        text: i.textContent?.trim() || ''
                    }));
                }""")
                print(f"Dropdown items: {len(all_menus)}")
                for mi in all_menus:
                    print(f"  '{mi['text']}'")
    
    browser.close()
    print("\nDone!")
