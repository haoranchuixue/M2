"""Create a new dashboard from workspace 'Quick Create' and capture the editor URL."""
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
    responses = {}
    def on_request(request):
        if '/de2api/' in request.url:
            api_calls.append({
                'method': request.method,
                'url': request.url.split('?')[0],
                'post_data': request.post_data
            })
    
    def on_response(response):
        url = response.url.split('?')[0]
        if '/de2api/' in url and ('Canvas' in url or 'saveCanvas' in url):
            try:
                body = response.json()
                responses[url] = body
                print(f"[RESPONSE] {url}: {json.dumps(body, ensure_ascii=False)[:300]}")
            except:
                pass
    
    page.on('request', on_request)
    page.on('response', on_response)
    
    # We should be on the workspace page. Click "仪表板" under quick create
    print("Looking for quick create dashboard button...")
    
    # From the workspace screenshot, there's a "仪表板" button in the left sidebar under "快速创建"
    # Let me find it
    quick_create_btns = page.locator('.ed-icon, span, div').all()
    for btn in quick_create_btns[:50]:
        txt = btn.inner_text().strip()
        if '仪表板' in txt and len(txt) < 10:
            parent_txt = ''
            try:
                parent = btn.locator('..')
                parent_txt = parent.inner_text()[:30].strip()
            except:
                pass
            cls = btn.get_attribute('class') or ''
            print(f"  Found '仪表板' element: class='{cls[:40]}', parent='{parent_txt}'")
    
    # Try the quick-create section
    page.screenshot(path='d:\\Projects\\m2\\scripts\\workspace_01.png')
    
    # The quick create section has buttons like "仪表板", "数据大屏", "数据集", "数据源"
    # These are in the left sidebar
    # Let me try clicking the "仪表板" quick create button (not the top nav)
    # It should be inside a section with "快速创建" text
    
    quick_section = page.locator('text="快速创建"')
    if quick_section.count() > 0:
        print("Found 快速创建 section")
        parent = quick_section.locator('..')
        # Find the 仪表板 button within the quick create section
        # Use XPath to find sibling or nearby elements
        
    # Try direct approach: click on the "仪表板" button in the quick create area
    # Based on the workspace screenshot, there should be a clickable "仪表板" button
    # Let me try different selectors
    
    api_calls.clear()
    
    # Use CSS to find buttons/links with "仪表板" near quick create
    # The quick create is a sidebar element with icon buttons
    # Let's click by coordinates: from the screenshot, "仪表板" under quick create is at roughly (63, 225)
    # But coordinates may differ. Let me be more precise.
    
    # Actually, let me try clicking the "仪表板" text that's inside the quick create section
    # There are multiple "仪表板" on the page: 1 in top nav, 1 in quick create
    all_dashboard_texts = page.locator('text="仪表板"').all()
    print(f"\nAll '仪表板' elements: {len(all_dashboard_texts)}")
    for i, el in enumerate(all_dashboard_texts):
        bbox = el.bounding_box()
        print(f"  #{i}: visible={el.is_visible()}, bbox={bbox}")
    
    # The one NOT in the top nav (y > 100) should be the quick create button
    for i, el in enumerate(all_dashboard_texts):
        bbox = el.bounding_box()
        if bbox and bbox['y'] > 150:
            print(f"\nClicking quick create 仪表板 at {bbox}")
            el.click()
            time.sleep(8)
            page.wait_for_load_state('networkidle', timeout=15000)
            
            print(f"URL: {page.url}")
            page.screenshot(path='d:\\Projects\\m2\\scripts\\new_dash_01.png')
            
            print(f"\nAPI calls: {len(api_calls)}")
            for c in api_calls:
                print(f"  {c['method']} {c['url']}")
                if c['post_data']:
                    print(f"    Body: {c['post_data'][:300]}")
            
            body = page.inner_text('body')[:500]
            print(f"\nPage: {body[:400]}")
            break
    
    browser.close()

print("Done.")
