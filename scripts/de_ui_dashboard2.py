"""Create dashboard by navigating through DataEase sidebar."""
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
    
    print(f"After login URL: {page.url}")
    
    # Now navigate to dashboard
    page.goto(f'{base}/#/dashboard/index', timeout=30000)
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    print(f"Dashboard URL: {page.url}")
    page.screenshot(path='d:/Projects/m2/scripts/de_dashboard2.png')
    
    # Check the sidebar menu
    sidebar = page.query_selector_all('[class*=sidebar] a, [class*=menu] a, [class*=nav] li')
    print(f"Sidebar items: {len(sidebar)}")
    for s in sidebar[:10]:
        text = s.inner_text().strip()
        if text:
            print(f"  '{text}'")
    
    # Try clicking "仪表板" in the sidebar
    dashboard_link = page.query_selector('text="仪表板"')
    if dashboard_link:
        print("\nClicking 仪表板 link...")
        dashboard_link.click()
        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=15000)
        print(f"URL: {page.url}")
        page.screenshot(path='d:/Projects/m2/scripts/de_dashboard3.png')
    
    api_log.clear()
    
    # Look for tree nodes on the dashboard page
    tree_nodes = page.query_selector_all('.ed-tree-node')
    print(f"\nTree nodes: {len(tree_nodes)}")
    for node in tree_nodes[:5]:
        content = node.query_selector('.ed-tree-node__content')
        if content:
            print(f"  Node: '{content.inner_text().strip()}'")
    
    # If no tree nodes, look for empty state with "create" button
    buttons = page.query_selector_all('button:visible')
    for b in buttons:
        text = b.inner_text().strip()
        if text and len(text) < 30:
            print(f"  Button: '{text}'")
    
    # Check page body for key text
    body_text = page.inner_text('body')[:2000]
    for kw in ['新建', '创建', '仪表板', '暂无', '空']:
        if kw in body_text:
            idx = body_text.index(kw)
            print(f"  Found '{kw}' at pos {idx}: ...{body_text[max(0,idx-20):idx+40]}...")
    
    # Try to find and click create/new button
    # In DataEase, the dashboard page might need a different path
    # Let me try the workbench first
    page.goto(f'{base}/#/workbranch/index', timeout=30000)
    time.sleep(3)
    print(f"\nWorkbranch URL: {page.url}")
    
    # Find sidebar menu items
    menu_items = page.query_selector_all('[class*=menu-item], [class*=nav-item], .router-link-active')
    for m in menu_items[:10]:
        text = m.inner_text().strip()
        href = m.get_attribute('href') or ''
        if text:
            print(f"  Menu: '{text}' href='{href}'")
    
    # Check for sidebar links
    links = page.query_selector_all('a')
    for l in links:
        href = l.get_attribute('href') or ''
        text = l.inner_text().strip()
        if ('dashboard' in href.lower() or 'panel' in href.lower() or '仪表板' in text) and text:
            print(f"  Link: '{text}' href='{href}'")
    
    # Let me try all possible dashboard routes
    for route in ['#/dashboard', '#/panel', '#/data/dashboard', '#/data/panel', '#/visualization/panel']:
        page.goto(f'{base}/{route}', timeout=15000)
        time.sleep(2)
        final_url = page.url
        has_tree = len(page.query_selector_all('.ed-tree-node')) > 0
        print(f"  Route {route}: final_url={final_url}, has_tree={has_tree}")
        if has_tree:
            break
    
    browser.close()
