"""Find and open the DSP Report dashboard editor."""
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
    print(f"Panel page URL: {page.url}")
    
    # Find DSP Report in the tree
    tree_nodes = page.query_selector_all('.ed-tree-node')
    print(f"Tree nodes: {len(tree_nodes)}")
    for node in tree_nodes:
        content = node.query_selector('.ed-tree-node__content')
        if content:
            text = content.inner_text().strip()
            print(f"  Node: '{text}'")
    
    api_log.clear()
    
    # Click on DSP Report to open it
    dsp_node = page.locator('.ed-tree-node__content:has-text("DSP Report")')
    if dsp_node.count() > 0:
        print("\nFound DSP Report node, double-clicking to edit...")
        dsp_node.first.dblclick()
        time.sleep(5)
        page.wait_for_load_state('networkidle', timeout=30000)
        print(f"URL after dblclick: {page.url}")
        page.screenshot(path='d:/Projects/m2/scripts/de_dsp_editor.png')
    else:
        # Try to find it
        print("\nDSP Report not found directly. Looking...")
        for node in tree_nodes:
            content = node.query_selector('.ed-tree-node__content')
            if content and 'DSP' in content.inner_text():
                content.dblclick()
                time.sleep(5)
                page.wait_for_load_state('networkidle', timeout=30000)
                print(f"URL: {page.url}")
                break
    
    # Check URL and content
    print(f"\nFinal URL: {page.url}")
    
    # Print API calls
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        print(f"  {entry['method']} {url}")
        if entry.get('body'):
            print(f"    Body: {str(entry['body'])[:300]}")
        if entry.get('response'):
            print(f"    Resp: {str(entry['response'])[:300]}")
    
    browser.close()
