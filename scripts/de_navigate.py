"""Navigate to tea dashboard to understand URL patterns, then check DSP."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    
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
    print("Logged in")
    
    # Navigate to dashboards
    page.goto(f'{base}/#/panel/index', timeout=60000)
    time.sleep(5)
    
    # Track navigation
    navigations = []
    def on_navigation(frame):
        navigations.append(frame.url)
    page.on('framenavigated', on_navigation)
    
    api_calls = []
    def on_req(request):
        if '/de2api/' in request.url:
            api_calls.append(f"REQ: {request.method} {request.url}")
    def on_resp(response):
        if '/de2api/' in response.url:
            try:
                body = response.json()
                api_calls.append(f"RESP: {response.url} -> code={body.get('code')}")
            except:
                api_calls.append(f"RESP: {response.url} -> status={response.status}")
    page.on('request', on_req)
    page.on('response', on_resp)
    
    # Click on 【官方示例】to expand it
    elements = page.query_selector_all('span')
    for el in elements:
        text = el.text_content()
        if text and '官方示例' in text:
            print(f"Expanding folder: {text}")
            el.click()
            break
    
    time.sleep(3)
    page.screenshot(path='d:/Projects/m2/scripts/ss_folder_expanded.png')
    
    # Now click on the tea dashboard inside the folder
    elements = page.query_selector_all('span')
    for el in elements:
        text = el.text_content()
        if text and '茶饮' in text:
            print(f"Clicking tea dashboard: {text}")
            el.click()
            break
    
    time.sleep(15)
    current_url = page.url
    print(f"URL after click: {current_url}")
    page.screenshot(path='d:/Projects/m2/scripts/ss_tea_loaded.png')
    
    print(f"\nAPI calls during tea dashboard load:")
    for c in api_calls:
        print(f"  {c}")
    
    api_calls.clear()
    
    # Now try DSP Report
    print(f"\n=== Now click DSP Report ===")
    page.goto(f'{base}/#/panel/index', timeout=60000)
    time.sleep(5)
    
    elements = page.query_selector_all('span')
    for el in elements:
        text = el.text_content()
        if text and text.strip() == 'DSP Report':
            print(f"Clicking: {text}")
            el.click()
            break
    
    time.sleep(15)
    current_url = page.url
    print(f"URL after click: {current_url}")
    page.screenshot(path='d:/Projects/m2/scripts/ss_dsp_loaded2.png')
    
    print(f"\nAPI calls during DSP dashboard load:")
    for c in api_calls:
        print(f"  {c}")
    
    browser.close()
