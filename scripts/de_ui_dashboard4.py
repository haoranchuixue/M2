"""Navigate to dashboard and create new via hover menu."""
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
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)
    
    # Navigate to dashboard via sidebar
    sidebar_items = page.query_selector_all('[class*=menu-item]')
    for item in sidebar_items:
        if '仪表板' in item.inner_text():
            item.click()
            time.sleep(3)
            break
    
    api_log.clear()
    
    # Find first tree node and use hover icon to create dashboard
    tree_nodes = page.query_selector_all('.ed-tree-node')
    print(f"Tree nodes: {len(tree_nodes)}")
    
    # Hover on 'mchat1' node
    for node in tree_nodes:
        content = node.query_selector('.ed-tree-node__content')
        if content:
            text = content.inner_text().strip()
            print(f"  Node: '{text}'")
            
            content.hover()
            time.sleep(1)
            
            hover_icons = node.query_selector_all('.hover-icon')
            print(f"  Hover icons: {len(hover_icons)}")
            
            if hover_icons and len(hover_icons) > 0:
                # Click first hover icon
                hover_icons[0].click()
                time.sleep(1)
                page.screenshot(path='d:/Projects/m2/scripts/de_hover_click.png')
                
                # Find ALL visible elements that might be menu items
                visible_text = page.evaluate("""() => {
                    const elements = document.querySelectorAll('*');
                    const results = [];
                    for (const el of elements) {
                        if (el.offsetParent !== null && el.textContent.trim().length > 0 && el.textContent.trim().length < 30) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                results.push({
                                    tag: el.tagName,
                                    text: el.textContent.trim(),
                                    class: el.className?.substring?.(0, 50) || '',
                                    x: rect.x,
                                    y: rect.y,
                                    w: rect.width,
                                    h: rect.height
                                });
                            }
                        }
                    }
                    return results;
                }""")
                
                # Filter for menu-like items
                for el in visible_text:
                    if '新建' in el['text'] or '创建' in el['text']:
                        print(f"  Found: '{el['text']}' at ({el['x']:.0f},{el['y']:.0f}) tag={el['tag']} class={el['class']}")
                
                # Click "新建仪表板" 
                new_db = page.query_selector('text="新建仪表板"')
                if new_db:
                    print("\nClicking '新建仪表板'...")
                    new_db.click()
                    time.sleep(5)
                    page.wait_for_load_state('networkidle', timeout=30000)
                    print(f"URL: {page.url}")
                    page.screenshot(path='d:/Projects/m2/scripts/de_new_db_created.png')
                else:
                    # Try clicking by coordinates - look for the dropdown
                    print("\n'新建仪表板' not found directly. Looking for alternatives...")
                    # Try locator
                    loc = page.locator('li:has-text("新建仪表板")')
                    count = loc.count()
                    print(f"  Locator count: {count}")
                    if count > 0:
                        loc.first.click()
                        time.sleep(5)
                        page.wait_for_load_state('networkidle', timeout=30000)
                        print(f"  URL: {page.url}")
                
                break
    
    # Print API calls
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        print(f"  POST {url}")
        if entry.get('body'):
            body_str = str(entry['body'])
            if len(body_str) > 5000:
                fname = 'dashboard_save_body.json'
                with open(f'd:/Projects/m2/scripts/{fname}', 'w', encoding='utf-8') as f:
                    f.write(body_str)
                print(f"    Body saved to {fname} ({len(body_str)} chars)")
            else:
                print(f"    Body: {body_str[:500]}")
        if entry.get('response'):
            print(f"    Resp: {str(entry['response'])[:500]}")
    
    browser.close()
