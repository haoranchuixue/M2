"""Edit DSP Report dashboard and add table chart component."""
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
    
    # Navigate to DSP Report dashboard
    page.goto(f'{base}/#/panel/index?dvId={dashboard_id}', timeout=30000, wait_until='domcontentloaded')
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)
    
    print(f"URL: {page.url}")
    page.screenshot(path='d:/Projects/m2/scripts/de_dsp_preview.png')
    
    api_log.clear()
    
    # Click "编辑" button
    edit_btn = page.locator('button:has-text("编辑")')
    if edit_btn.count() > 0:
        print("Clicking '编辑' button...")
        edit_btn.first.click()
        time.sleep(5)
        page.wait_for_load_state('networkidle', timeout=30000)
        print(f"URL after edit: {page.url}")
        page.screenshot(path='d:/Projects/m2/scripts/de_dsp_editor2.png')
        
        # In edit mode, look for the toolbar to add a chart
        body_text = page.inner_text('body')[:2000]
        print(f"\nBody text: {body_text[:500]}")
        
        # Look for "图表" or "添加" buttons in toolbar
        for kw in ['图表', '添加', '视图', '表格']:
            if kw in body_text:
                idx = body_text.index(kw)
                print(f"  Found '{kw}': ...{body_text[max(0,idx-20):idx+40]}...")
        
        # Find all visible buttons
        buttons = page.query_selector_all('button:visible, [class*=toolbar] *:visible')
        for b in buttons[:20]:
            text = b.inner_text().strip()
            if text and len(text) < 30:
                tag = b.evaluate('e => e.tagName')
                cls = b.get_attribute('class') or ''
                print(f"  {tag}: '{text}' (class={cls[:60]})")
        
        # Print API calls for edit mode
        print(f"\n=== API calls ({len(api_log)}) ===")
        for entry in api_log:
            url = entry['url']
            if any(kw in url.lower() for kw in ['visual', 'chart', 'canvas', 'view', 'find']):
                print(f"\n  POST {url}")
                if entry.get('body'):
                    print(f"    Body: {str(entry['body'])[:300]}")
                if entry.get('response'):
                    resp = str(entry['response'])
                    if len(resp) > 5000:
                        fname = f"edit2_{url.replace('/', '_').strip('_')}.json"
                        with open(f'd:/Projects/m2/scripts/{fname}', 'w', encoding='utf-8') as f:
                            f.write(resp)
                        print(f"    Resp saved to {fname} ({len(resp)} chars)")
                    else:
                        print(f"    Resp: {resp[:500]}")
    else:
        print("Edit button not found")
        buttons = page.query_selector_all('button:visible')
        for b in buttons:
            print(f"  Button: '{b.inner_text().strip()}'")
    
    browser.close()
