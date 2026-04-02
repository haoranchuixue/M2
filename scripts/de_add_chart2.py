"""Add table chart to dashboard - capture actual API from UI."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
api_log = []

def on_request(request):
    if '/de2api/' in request.url and request.method in ['POST', 'PUT']:
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
    if '/de2api/' in response.url:
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
    time.sleep(1)
    inputs = page.query_selector_all('input')
    inputs[0].fill('admin')
    inputs[1].fill('DataEase@123456')
    page.query_selector('button').click()
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)
    
    dashboard_id = '1236050016221663232'
    
    # Navigate to dashboard editor
    print(f"Opening dashboard editor...")
    page.goto(f'{base}/#/dashboard/{dashboard_id}', timeout=60000, wait_until='domcontentloaded')
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)
    
    print(f"URL: {page.url}")
    page.screenshot(path='d:/Projects/m2/scripts/de_editor.png')
    
    api_log.clear()
    
    # Look for add chart button or component panel
    body_text = page.inner_text('body')[:2000]
    print(f"\nPage text preview: {body_text[:500]}")
    
    # Look for toolbar buttons
    buttons = page.query_selector_all('button:visible')
    for b in buttons:
        text = b.inner_text().strip()
        if text and len(text) < 30:
            print(f"  Button: '{text}'")
    
    # Look for icons/elements related to adding charts
    for selector in ['[class*=chart]', '[class*=view]', '[class*=add]', '[class*=toolbar]']:
        els = page.query_selector_all(f'{selector}:visible')
        if els and len(els) < 20:
            for el in els[:5]:
                cls = el.get_attribute('class') or ''
                text = el.inner_text()[:30]
                print(f"  {selector}: class={cls[:60]}, text='{text}'")
    
    # Try to find "添加图表" or similar button
    chart_add = page.locator('text=图表').first
    if chart_add.is_visible():
        print("\nFound '图表' element")
    
    # Check for drag panel or component list
    panels = page.query_selector_all('[class*=panel]:visible, [class*=aside]:visible')
    for panel in panels[:5]:
        text = panel.inner_text()[:200]
        if text.strip():
            print(f"\n  Panel: {text[:100]}")
    
    # Print API calls after loading editor
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        if any(kw in url.lower() for kw in ['visual', 'chart', 'canvas', 'save', 'update']):
            print(f"\n  {entry['method']} {url}")
            if entry.get('body'):
                body_str = str(entry['body'])
                if len(body_str) > 3000:
                    fname = f"editor_{url.replace('/', '_').strip('_')}.json"
                    with open(f'd:/Projects/m2/scripts/{fname}', 'w', encoding='utf-8') as f:
                        f.write(body_str)
                    print(f"    Body saved to {fname} ({len(body_str)} chars)")
                else:
                    print(f"    Body: {body_str[:500]}")
            if entry.get('response'):
                resp_str = str(entry['response'])
                print(f"    Resp: {resp_str[:300]}")
    
    browser.close()
