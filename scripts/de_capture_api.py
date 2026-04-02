"""Capture DataEase API calls using Playwright."""
from playwright.sync_api import sync_playwright
import json
import time

captured_requests = []

def capture_request(request):
    if '/de2api/' in request.url or '/api/' in request.url:
        captured_requests.append({
            'url': request.url,
            'method': request.method,
            'headers': dict(request.headers),
        })

def capture_response(response):
    url = response.url
    if '/de2api/' in url or '/api/' in url:
        for req in captured_requests:
            if req['url'] == url:
                try:
                    req['status'] = response.status
                    body = response.body()
                    req['body'] = body.decode('utf-8', errors='replace')[:500]
                except:
                    pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    page.on('request', capture_request)
    page.on('response', capture_response)
    
    print("Navigating to DataEase...")
    page.goto('http://47.236.78.123:8100/', timeout=30000)
    page.wait_for_load_state('networkidle', timeout=30000)
    
    # Login
    inputs = page.query_selector_all('input')
    if len(inputs) >= 2:
        inputs[0].fill('admin')
        time.sleep(0.3)
        inputs[1].fill('DataEase@123456')
        time.sleep(0.3)
    
    login_btn = page.query_selector('button')
    if login_btn:
        login_btn.click()
    
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)
    
    print(f"After login URL: {page.url}")
    
    # Navigate to data source page
    print("\nNavigating to data source management...")
    # Try clicking on the datasource menu item
    page.goto('http://47.236.78.123:8100/#/data/datasource', timeout=30000)
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    print(f"Current URL: {page.url}")
    page.screenshot(path='d:/Projects/m2/scripts/de_datasource.png')
    
    # Navigate to dataset page
    print("\nNavigating to dataset management...")
    page.goto('http://47.236.78.123:8100/#/data/dataset', timeout=30000)
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    print(f"Current URL: {page.url}")
    page.screenshot(path='d:/Projects/m2/scripts/de_dataset.png')
    
    # Print captured API calls
    print(f"\n=== Captured {len(captured_requests)} API calls ===")
    for req in captured_requests:
        status = req.get('status', '?')
        body_preview = req.get('body', '')[:200]
        token_header = req.get('headers', {}).get('x-de-token', 'N/A')[:50]
        print(f"\n  {req['method']} {req['url']}")
        print(f"    Status: {status}, Token: {token_header}")
        if body_preview:
            print(f"    Body: {body_preview}")
    
    browser.close()
