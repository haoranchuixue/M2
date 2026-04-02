"""Screenshot the dashboard after style fix."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
dashboard_id = 1236050016221663232

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    
    console_msgs = []
    def on_console(msg):
        if msg.type in ('error',):
            console_msgs.append(msg.text[:200])
    page.on('console', on_console)
    
    api_responses = []
    def on_response(response):
        url = response.url.split('?')[0]
        if '/de2api/' in url and ('getData' in url or 'findById' in url):
            try:
                body = response.json()
                code = body.get('code', 'N/A')
                data_preview = str(body.get('data', ''))[:100]
                api_responses.append(f"{response.status} {url.replace(base,'')} code={code}")
            except:
                api_responses.append(f"{response.status} {url.replace(base,'')}")
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
    
    # Navigate to dashboard
    page.goto(f'{base}/#/panel/index?dvId={dashboard_id}', timeout=60000)
    time.sleep(15)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    page.screenshot(path='d:\\Projects\\m2\\scripts\\dsp_report_v3.png')
    print(f"URL: {page.url}")
    
    print(f"\nAPI responses ({len(api_responses)}):")
    for r in api_responses:
        print(f"  {r}")
    
    if console_msgs:
        print(f"\nConsole errors ({len(console_msgs)}):")
        for m in console_msgs[:10]:
            print(f"  {m}")
    
    body = page.inner_text('body')[:800]
    print(f"\nBody: {body[:500]}")
    
    browser.close()

print("Done.")
