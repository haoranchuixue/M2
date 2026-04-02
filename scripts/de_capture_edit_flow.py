"""Capture the full edit flow for the tea dashboard to understand chart creation."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
tea_id = 985192741891870720

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
    
    all_api_calls = []
    def on_request(request):
        if '/de2api/' in request.url:
            all_api_calls.append({
                'method': request.method,
                'url': request.url.split('?')[0],
                'full_url': request.url,
                'post_data': request.post_data
            })
    page.on('request', on_request)
    
    # Navigate to dashboard page and click on tea dashboard
    page.click('text="仪表板"')
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    folder = page.locator('text="【官方示例】"').first
    folder.click()
    time.sleep(1)
    
    tea = page.locator('text="连锁茶饮销售看板"').first
    tea.click()
    time.sleep(3)
    all_api_calls.clear()
    
    # Now hover over the tea dashboard and click the edit icon
    node = page.locator('.custom-tree-node:has-text("连锁茶饮销售看板")').first
    node.hover()
    time.sleep(0.5)
    
    # Click the edit icon
    icon_more = node.locator('.icon-more').first
    edit_icon = icon_more.locator('.ed-icon.hover-icon').first
    edit_icon.click(force=True)
    
    # Wait for navigation/editor to load
    time.sleep(10)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    print(f"URL: {page.url}")
    page.screenshot(path='d:\\Projects\\m2\\scripts\\tea_edit_01.png')
    
    print(f"\nAPI calls captured ({len(all_api_calls)}):")
    for c in all_api_calls:
        print(f"  {c['method']} {c['url']}")
        if c['post_data']:
            pd = c['post_data'][:300]
            print(f"    Body: {pd}")
    
    body = page.inner_text('body')[:500]
    print(f"\nPage content: {body[:400]}")
    
    browser.close()

print("Done.")
