"""Click on DSP Report tree node properly to trigger dashboard preview."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
dashboard_id = '1236050016221663232'
api_log = []

def on_request(request):
    if '/de2api/' in request.url and request.method == 'POST':
        try:
            body = request.post_data
        except:
            body = None
        api_log.append({
            'url': request.url.replace(base, ''),
            'method': request.method,
            'body': body,
        })

def on_response(response):
    if '/de2api/' in response.url and response.request.method == 'POST':
        for entry in reversed(api_log):
            if entry['url'] == response.url.replace(base, '') and 'response' not in entry:
                try:
                    entry['response'] = response.body().decode('utf-8', errors='replace')
                    entry['status'] = response.status
                except:
                    pass
                break

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = context.new_page()
    page.on('request', on_request)
    page.on('response', on_response)
    
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
    
    # Navigate to dashboard section
    sidebar_items = page.query_selector_all('[class*=menu-item]')
    for item in sidebar_items:
        if '仪表板' in item.inner_text():
            item.click()
            time.sleep(3)
            break
    
    page.wait_for_load_state('networkidle', timeout=15000)
    api_log.clear()
    
    # Find and click DSP Report tree node with text content
    page.wait_for_selector('.ed-tree-node', timeout=10000)
    
    # Use locator to find the specific tree label
    dsp_label = page.locator('.ed-tree-node__label:has-text("DSP Report")')
    if dsp_label.count() > 0:
        print(f"Found DSP Report label")
        dsp_label.first.click()
        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=15000)
        
        print(f"URL after label click: {page.url}")
        
        # Check for any visible preview or buttons
        body = page.inner_text('body')[:1000]
        has_edit = '编辑' in body
        has_preview = '预览' in body
        has_empty = '请在左侧选择仪表板' in body
        print(f"Has edit: {has_edit}, Has preview: {has_preview}, Empty: {has_empty}")
        
        if has_edit:
            edit_btn = page.locator('button:has-text("编辑")')
            edit_btn.first.click()
            time.sleep(5)
        elif has_empty:
            # The dashboard is at root level and might not be supported for preview
            # Let me try to use the hover "edit" icon
            print("\nLooking for hover edit icon...")
            tree_nodes = page.query_selector_all('.ed-tree-node')
            for node in tree_nodes:
                content = node.query_selector('.ed-tree-node__content')
                if content and 'DSP Report' in content.inner_text():
                    content.hover()
                    time.sleep(1)
                    
                    hover_icons = node.query_selector_all('.hover-icon')
                    print(f"Hover icons: {len(hover_icons)}")
                    
                    # The second icon should be "more options" with edit
                    if len(hover_icons) >= 2:
                        hover_icons[1].click()
                        time.sleep(1)
                        
                        # Check dropdown
                        dd = page.query_selector_all('.ed-dropdown-menu:visible')
                        for menu in dd:
                            items = menu.query_selector_all('li')
                            for item in items:
                                t = item.inner_text().strip()
                                print(f"  Menu: '{t}'")
                                if '编辑' in t:
                                    item.click()
                                    time.sleep(5)
                                    page.wait_for_load_state('networkidle', timeout=30000)
                                    break
                    break
    
    print(f"\nFinal URL: {page.url}")
    page.screenshot(path='d:/Projects/m2/scripts/de_final_edit.png')
    
    # Print API calls
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        print(f"  POST {url}")
        if entry.get('body'):
            print(f"    Body: {str(entry['body'])[:200]}")
        if entry.get('response'):
            resp = str(entry['response'])
            if len(resp) > 5000:
                fname = f"click_{url.replace('/', '_').strip('_')}.json"
                with open(f'd:/Projects/m2/scripts/{fname}', 'w', encoding='utf-8') as f:
                    f.write(resp)
                print(f"    Resp saved to {fname}")
            else:
                print(f"    Resp: {resp[:300]}")
    
    browser.close()
