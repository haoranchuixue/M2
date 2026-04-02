"""Login to DataEase using Playwright and get the auth token."""
from playwright.sync_api import sync_playwright
import json
import time

def login_and_get_token():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        print("Navigating to DataEase...")
        page.goto('http://47.236.78.123:8100/', timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)
        
        print(f"Page title: {page.title()}")
        print(f"Current URL: {page.url}")
        
        # Wait for login form
        page.wait_for_selector('input', timeout=15000)
        
        # Take screenshot before login
        page.screenshot(path='d:/Projects/m2/scripts/de_before_login.png')
        print("Screenshot saved: de_before_login.png")
        
        # Find and fill username
        inputs = page.query_selector_all('input')
        print(f"Found {len(inputs)} input fields")
        for i, inp in enumerate(inputs):
            input_type = inp.get_attribute('type') or ''
            placeholder = inp.get_attribute('placeholder') or ''
            print(f"  Input {i}: type={input_type}, placeholder={placeholder}")
        
        # Fill login form
        # Username is usually the first input
        if len(inputs) >= 2:
            inputs[0].fill('admin')
            time.sleep(0.5)
            inputs[1].fill('DataEase@123456')
            time.sleep(0.5)
        
        # Click login button
        login_btn = page.query_selector('button') or page.query_selector('[class*=login]')
        if login_btn:
            print(f"Clicking login button: {login_btn.inner_text()}")
            login_btn.click()
        
        # Wait for navigation/login
        time.sleep(5)
        page.wait_for_load_state('networkidle', timeout=30000)
        
        print(f"After login URL: {page.url}")
        page.screenshot(path='d:/Projects/m2/scripts/de_after_login.png')
        print("Screenshot saved: de_after_login.png")
        
        # Get token from localStorage
        token = page.evaluate("() => localStorage.getItem('user.token')")
        exp = page.evaluate("() => localStorage.getItem('user.exp')")
        
        # Also get all localStorage items
        all_storage = page.evaluate("""() => {
            const items = {};
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                items[key] = localStorage.getItem(key);
            }
            return items;
        }""")
        
        print(f"\nToken: {token}")
        print(f"Exp: {exp}")
        print(f"\nAll localStorage items:")
        for k, v in all_storage.items():
            val_str = str(v)[:100]
            print(f"  {k}: {val_str}")
        
        # Save token to file
        if token:
            with open('d:/Projects/m2/scripts/de_token.json', 'w') as f:
                json.dump({'token': token, 'exp': exp, 'storage': all_storage}, f, indent=2)
            print("\nToken saved to de_token.json")
        
        browser.close()

if __name__ == '__main__':
    login_and_get_token()
