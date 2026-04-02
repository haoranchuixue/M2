"""Open DSP Report dashboard and enter edit mode."""
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
    
    # Click DSP Report
    dsp = page.locator('.ed-tree-node__content:has-text("DSP Report")')
    if dsp.count() > 0:
        dsp.first.click()
        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=15000)
        print(f"After click URL: {page.url}")
        page.screenshot(path='d:/Projects/m2/scripts/de_dsp_click.png')
        
        # Look for edit button
        body = page.inner_text('body')
        for kw in ['编辑', '进入', 'Edit']:
            if kw in body:
                idx = body.index(kw)
                print(f"  Found '{kw}' at: ...{body[max(0,idx-30):idx+30]}...")
        
        # Find all visible buttons
        buttons = page.query_selector_all('button:visible')
        for b in buttons:
            text = b.inner_text().strip()
            if text:
                print(f"  Button: '{text}'")
                if '编辑' in text:
                    print(f"  --> Clicking edit button")
                    b.click()
                    time.sleep(5)
                    page.wait_for_load_state('networkidle', timeout=30000)
                    break
        
        # Check URL
        print(f"\nFinal URL: {page.url}")
        page.screenshot(path='d:/Projects/m2/scripts/de_dsp_edit.png')
        
        # Look for toolbar/icons
        icons = page.query_selector_all('[class*=edit]:visible, [class*=toolbar]:visible')
        for icon in icons[:10]:
            cls = icon.get_attribute('class') or ''
            text = icon.inner_text()[:30]
            print(f"  Icon: class={cls[:60]}, text='{text}'")
    
    # Print API calls
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        if any(kw in url.lower() for kw in ['visual', 'chart', 'canvas', 'view', 'find']):
            print(f"\n  POST {url}")
            if entry.get('body'):
                print(f"    Body: {str(entry['body'])[:300]}")
            if entry.get('response'):
                resp = str(entry['response'])
                if len(resp) > 3000:
                    fname = f"edit_{url.replace('/', '_').strip('_')}.json"
                    with open(f'd:/Projects/m2/scripts/{fname}', 'w', encoding='utf-8') as f:
                        f.write(resp)
                    print(f"    Resp saved to {fname}")
                else:
                    print(f"    Resp: {resp[:300]}")
    
    browser.close()
