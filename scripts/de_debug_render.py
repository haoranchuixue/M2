"""Debug rendering - compare working tea dashboard vs DSP Report in edit mode."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
tea_id = '985192741891870720'
dsp_id = '1236050016221663232'

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
    
    # Intercept API calls to see what's happening
    api_responses = []
    def on_response(response):
        url = response.url
        if '/de2api/' in url and ('chartData' in url or 'findById' in url or 'getData' in url):
            try:
                body = response.json()
                code = body.get('code', 'N/A')
                msg = str(body.get('msg', ''))[:100]
                api_responses.append(f"{url}: code={code}, msg={msg}")
            except:
                api_responses.append(f"{url}: status={response.status}")
    page.on('response', on_response)
    
    # Open tea dashboard first (known working)
    print("\n=== Opening Tea Dashboard ===")
    page.goto(f'{base}/#/panel/index', timeout=60000)
    time.sleep(3)
    
    elements = page.query_selector_all('span')
    for el in elements:
        text = el.text_content()
        if text and '茶饮' in text:
            print(f"Clicking: {text}")
            el.click()
            break
    
    time.sleep(15)
    page.screenshot(path='d:/Projects/m2/scripts/ss_tea.png')
    print(f"Tea API responses: {len(api_responses)}")
    for r in api_responses:
        print(f"  {r}")
    
    api_responses.clear()
    
    # Open DSP Report dashboard
    print("\n=== Opening DSP Report ===")
    page.goto(f'{base}/#/panel/index', timeout=60000)
    time.sleep(3)
    
    elements = page.query_selector_all('span')
    for el in elements:
        text = el.text_content()
        if text and text.strip() == 'DSP Report':
            print(f"Clicking: {text}")
            el.click()
            break
    
    time.sleep(30)
    page.screenshot(path='d:/Projects/m2/scripts/ss_dsp_view.png')
    print(f"DSP API responses: {len(api_responses)}")
    for r in api_responses:
        print(f"  {r}")
    
    api_responses.clear()
    
    # Also try direct edit URL
    print("\n=== DSP Edit mode ===")
    page.goto(f'{base}/#/dvCanvas?dvId={dsp_id}&opt=edit', timeout=60000)
    time.sleep(20)
    page.screenshot(path='d:/Projects/m2/scripts/ss_dsp_edit.png')
    print(f"DSP Edit API responses: {len(api_responses)}")
    for r in api_responses:
        print(f"  {r}")
    
    # Check console errors
    console_msgs = []
    page.on('console', lambda msg: console_msgs.append(f"[{msg.type}] {msg.text[:200]}"))
    time.sleep(5)
    if console_msgs:
        print(f"\nConsole messages: {len(console_msgs)}")
        for cm in console_msgs[:10]:
            print(f"  {cm}")
    
    browser.close()
