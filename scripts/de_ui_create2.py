"""Click the create dataset buttons in DataEase UI."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
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
    page = browser.new_page()
    page.on('request', on_request)
    page.on('response', on_response)
    
    # Login
    page.goto(f'{base}/', timeout=30000)
    page.wait_for_load_state('networkidle', timeout=30000)
    inputs = page.query_selector_all('input')
    inputs[0].fill('admin')
    inputs[1].fill('DataEase@123456')
    page.query_selector('button').click()
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    # Navigate to dataset page
    page.goto(f'{base}/#/data/dataset', timeout=30000)
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    api_log.clear()
    
    # Find DSP Report node and click the hover icon buttons
    tree_nodes = page.query_selector_all('.ed-tree-node')
    for node in tree_nodes:
        content = node.query_selector('.ed-tree-node__content')
        if content and 'DSP Report' in content.inner_text():
            content.hover()
            time.sleep(1)
            
            # Get the hover icon buttons (ed-icon hover-icon)
            hover_icons = node.query_selector_all('.hover-icon')
            print(f"Hover icons: {len(hover_icons)}")
            
            for i, icon in enumerate(hover_icons):
                # Get tooltip text
                tooltip = icon.get_attribute('aria-describedby') or ''
                print(f"  Icon {i}: tooltip_ref={tooltip}")
                
                # Hover to trigger tooltip
                icon.hover()
                time.sleep(0.5)
                
                # Check for tooltips
                tooltips = page.query_selector_all('.ed-popper, [class*=tooltip], [role=tooltip]')
                for tt in tooltips:
                    if tt.is_visible():
                        tt_text = tt.inner_text().strip()
                        if tt_text:
                            print(f"    Tooltip: '{tt_text}'")
            
            # Click the first hover icon (likely "add dataset")
            if hover_icons:
                print(f"\nClicking first hover icon...")
                hover_icons[0].click()
                time.sleep(2)
                page.screenshot(path='d:/Projects/m2/scripts/de_click_icon1.png')
                
                # Check for any new dialog, dropdown, or page change
                visible_dialogs = page.query_selector_all('[class*=dialog], [class*=drawer], [class*=dropdown-menu]')
                for d in visible_dialogs:
                    if d.is_visible():
                        text = d.inner_text()[:300]
                        print(f"  Visible element: {text}")
                
                # Check page URL
                print(f"  URL after click: {page.url}")
                
                # Check for new inputs
                new_inputs = page.query_selector_all('input:visible, textarea:visible')
                for inp in new_inputs:
                    ph = inp.get_attribute('placeholder') or ''
                    tp = inp.get_attribute('type') or ''
                    print(f"  Input: type={tp}, placeholder={ph}")
            
            # Go back and try second hover icon
            page.goto(f'{base}/#/data/dataset', timeout=30000)
            time.sleep(3)
            api_log.clear()
            
            # Re-find the node
            tree_nodes2 = page.query_selector_all('.ed-tree-node')
            for node2 in tree_nodes2:
                content2 = node2.query_selector('.ed-tree-node__content')
                if content2 and 'DSP Report' in content2.inner_text():
                    content2.hover()
                    time.sleep(1)
                    hover_icons2 = node2.query_selector_all('.hover-icon')
                    if len(hover_icons2) > 1:
                        print(f"\nClicking second hover icon...")
                        # First hover to see tooltip
                        hover_icons2[1].hover()
                        time.sleep(0.5)
                        tooltips = page.query_selector_all('[role=tooltip], .ed-popper')
                        for tt in tooltips:
                            if tt.is_visible():
                                print(f"  Tooltip: '{tt.inner_text().strip()}'")
                        
                        hover_icons2[1].click()
                        time.sleep(2)
                        page.screenshot(path='d:/Projects/m2/scripts/de_click_icon2.png')
                        
                        # Check for new elements
                        visible = page.query_selector_all('[class*=dialog]:visible, [class*=drawer]:visible, [class*=dropdown-menu]:visible')
                        for v in visible:
                            text = v.inner_text()[:300]
                            if text.strip():
                                print(f"  Visible element: {text}")
                        
                        # Check dropdowns
                        dropdowns = page.query_selector_all('.ed-dropdown-menu')
                        for dd in dropdowns:
                            if dd.is_visible():
                                items = dd.query_selector_all('li')
                                for item in items:
                                    t = item.inner_text().strip()
                                    if t:
                                        print(f"  Dropdown item: '{t}'")
                    break
            break
    
    # Print API calls
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        if 'dataset' in url.lower() or 'table' in url.lower():
            print(f"  POST {url}")
            if entry.get('body'):
                print(f"    Body: {str(entry['body'])[:300]}")
            if entry.get('response'):
                print(f"    Resp: {str(entry['response'])[:300]}")
    
    browser.close()
