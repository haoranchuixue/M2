"""Click quick create dashboard button by finding the correct element."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    
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
    
    api_calls = []
    def on_request(request):
        if '/de2api/' in request.url:
            api_calls.append({
                'method': request.method,
                'url': request.url.split('?')[0],
                'post_data': request.post_data
            })
    page.on('request', on_request)
    
    # Find the quick create section and examine its HTML structure
    html = page.evaluate("""() => {
        const quickCreate = document.querySelector('.quick-create') 
                          || Array.from(document.querySelectorAll('*')).find(
                               e => e.textContent.includes('快速创建') && e.children.length > 0 && e.children.length < 10
                             );
        return quickCreate ? quickCreate.outerHTML : 'not found';
    }""")
    print(f"Quick create HTML:\n{html[:3000]}")
    
    # Try using evaluate to click the quick create dashboard
    print("\n\nAttempting to click via JS...")
    result = page.evaluate("""() => {
        // Find all items in quick create
        const items = document.querySelectorAll('.item');
        for (const item of items) {
            if (item.textContent.includes('仪表板') && item.querySelector('svg, .ed-icon')) {
                item.click();
                return 'clicked: ' + item.textContent.trim();
            }
        }
        return 'not found';
    }""")
    print(f"Click result: {result}")
    
    time.sleep(8)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    print(f"URL after click: {page.url}")
    page.screenshot(path='d:\\Projects\\m2\\scripts\\new_dash_02.png')
    
    print(f"\nAPI calls: {len(api_calls)}")
    for c in api_calls:
        print(f"  {c['method']} {c['url']}")
        if c['post_data']:
            print(f"    Body: {c['post_data'][:300]}")
    
    body = page.inner_text('body')[:500]
    print(f"\nPage: {body[:400]}")
    
    browser.close()

print("Done.")
