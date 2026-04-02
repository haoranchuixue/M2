"""Open existing dataset in edit mode, capture save payload for reference."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    
    save_reqs = []
    def handle_req(req):
        if 'datasetTree' in req.url and req.method == 'POST':
            save_reqs.append({
                'url': req.url,
                'body': req.post_data
            })
    page.on('request', handle_req)
    
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
    
    # Navigate to dataset page
    page.goto(f'{base}/#/data/dataset', timeout=30000, wait_until='domcontentloaded')
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    # Expand DSP Report group
    dsp_el = page.query_selector('span.label-tooltip:has-text("DSP Report")')
    if not dsp_el:
        dsp_el = page.query_selector('span:has-text("DSP Report")')
    if dsp_el:
        # Click the expand arrow first
        expand_icon = page.evaluate("""(el) => {
            const node = el.closest('.ed-tree-node');
            const arrow = node?.querySelector('.ed-tree-node__expand-icon');
            if (arrow) {
                arrow.click();
                return 'clicked expand';
            }
            return 'no expand icon';
        }""", dsp_el)
        print(f"Expand: {expand_icon}")
        time.sleep(2)
        
        # Look for dataset "DSP Report Data" inside the group
        ds_el = page.query_selector('span.label-tooltip:has-text("DSP Report Data")')
        if not ds_el:
            ds_el = page.query_selector('span:has-text("DSP Report Data")')
        
        if ds_el:
            print("Found 'DSP Report Data', hovering to find edit icon...")
            ds_el.hover()
            time.sleep(1)
            
            # Look for edit icon
            hover_icons = page.query_selector_all('.ed-icon.hover-icon')
            print(f"Hover icons: {len(hover_icons)}")
            
            # Click the first hover icon (should be edit)
            if hover_icons:
                hover_icons[0].click()
                time.sleep(1)
                
                # Check if a dropdown appeared
                menu_items = page.evaluate("""() => {
                    const items = document.querySelectorAll('.ed-dropdown-menu__item');
                    return Array.from(items).filter(i => i.offsetParent !== null).map(i => i.textContent?.trim() || '');
                }""")
                print(f"Menu items: {menu_items}")
                
                # Look for "编辑" or click the edit option
                if menu_items:
                    for item_text in menu_items:
                        if '编辑' in item_text:
                            edit_item = page.query_selector(f'.ed-dropdown-menu__item:has-text("{item_text}")')
                            if edit_item:
                                print(f"Clicking '{item_text}'...")
                                edit_item.click()
                                time.sleep(3)
                                break
                
                page.wait_for_load_state('networkidle', timeout=15000)
                print(f"URL: {page.url}")
                page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds_edit.png')
                
                # If we're in the edit form, the page should be dataset-form
                if 'dataset-form' in page.url:
                    print("In dataset form! Looking for dsp_report in the center area...")
                    time.sleep(3)
                    page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds_edit_form.png')
                    
                    # Just click save to capture the save payload
                    save_btn = page.query_selector('button:has-text("保存")')
                    if save_btn and save_btn.is_visible():
                        # Check if button is enabled
                        disabled = save_btn.evaluate("el => el.disabled")
                        print(f"Save button disabled: {disabled}")
                        if not disabled:
                            print("Clicking save to capture payload...")
                            save_btn.click()
                            time.sleep(5)
        else:
            print("DSP Report Data dataset not found")
            # List visible tree nodes
            nodes = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('.ed-tree-node .label-tooltip')).map(n => n.textContent?.trim() || '');
            }""")
            print(f"Tree nodes: {nodes}")
    
    # Print captured API calls
    print(f"\n=== Captured {len(save_reqs)} API requests ===")
    for req in save_reqs:
        print(f"\nURL: {req['url']}")
        if req['body']:
            try:
                body = json.loads(req['body'])
                # Save full body for reference
                with open('d:/Projects/m2/scripts/captured_save_payload.json', 'w', encoding='utf-8') as f:
                    json.dump(body, f, indent=2, ensure_ascii=False)
                
                print(f"Name: {body.get('name')}")
                print(f"Keys: {list(body.keys())}")
                
                info_str = body.get('info', '')
                if isinstance(info_str, str) and info_str:
                    try:
                        info = json.loads(info_str)
                        if isinstance(info, list) and len(info) > 0:
                            ds = info[0].get('currentDs', {})
                            print(f"DS type: {ds.get('type')}")
                            print(f"DS info: {ds.get('info', '')[:200]}")
                    except:
                        pass
            except:
                print(f"Raw body: {req['body'][:500]}")
    
    browser.close()
    print("\nDone!")
