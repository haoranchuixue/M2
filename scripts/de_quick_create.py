"""Create dashboard via workbranch quick create."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time
import requests

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
    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = context.new_page()
    page.on('request', on_request)
    page.on('response', on_response)
    
    # Login
    page.goto(f'{base}/', timeout=30000)
    page.wait_for_load_state('networkidle', timeout=30000)
    page.wait_for_selector('input[type="text"]', timeout=10000)
    time.sleep(1)
    inputs = page.query_selector_all('input')
    inputs[0].fill('admin')
    inputs[1].fill('DataEase@123456')
    page.query_selector('button').click()
    
    try:
        page.wait_for_url('**/workbranch/**', timeout=15000)
    except:
        pass
    time.sleep(5)
    
    print(f"URL: {page.url}")
    
    # On the workbranch page, find "快速创建" section and click "仪表板"
    api_log.clear()
    
    # Look for "快速创建" section
    quick_create = page.locator('text=快速创建').first
    if quick_create.is_visible():
        print("Found '快速创建' section")
    
    # Find the "仪表板" option in quick create
    # It's typically a card or button labeled "仪表板"
    # Let's look for it in the quick-create area
    quick_items = page.evaluate("""() => {
        const items = [];
        document.querySelectorAll('*').forEach(el => {
            if (el.textContent.includes('仪表板') && 
                el.textContent.trim().length < 15 &&
                el.offsetParent !== null) {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    items.push({
                        tag: el.tagName,
                        text: el.textContent.trim(),
                        class: el.className?.substring?.(0, 80) || '',
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        w: Math.round(rect.width),
                        h: Math.round(rect.height)
                    });
                }
            }
        });
        return items;
    }""")
    
    print(f"\n'仪表板' elements: {len(quick_items)}")
    for item in quick_items:
        print(f"  {item['tag']} '{item['text']}' at ({item['x']},{item['y']}) {item['w']}x{item['h']} class={item['class']}")
    
    # Find the one in the quick-create area (typically in the middle of the page, not sidebar)
    # Sidebar items are usually on the left (x < 200)
    for item in quick_items:
        if item['x'] > 200 and '仪表板' in item['text'] and item['text'] == '仪表板':
            print(f"\nClicking quick-create '仪表板' at ({item['x']},{item['y']})...")
            page.mouse.click(item['x'] + item['w']/2, item['y'] + item['h']/2)
            time.sleep(5)
            page.wait_for_load_state('networkidle', timeout=30000)
            break
    
    print(f"\nURL after click: {page.url}")
    page.screenshot(path='d:/Projects/m2/scripts/de_quick_create.png')
    
    # Print API calls
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        body_str = str(entry.get('body', '') or '')
        resp_str = str(entry.get('response', '') or '')
        if any(kw in url.lower() for kw in ['visual', 'panel', 'save', 'chart', 'create', 'canvas']):
            print(f"\n  POST {url}")
            if body_str:
                if len(body_str) > 5000:
                    fname = 'quick_create_body.json'
                    with open(f'd:/Projects/m2/scripts/{fname}', 'w', encoding='utf-8') as f:
                        f.write(body_str)
                    print(f"    Body saved to {fname} ({len(body_str)} chars)")
                    print(f"    Preview: {body_str[:500]}")
                else:
                    print(f"    Body: {body_str[:500]}")
            if resp_str:
                print(f"    Resp: {resp_str[:500]}")
    
    browser.close()
