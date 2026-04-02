"""Get StarRocks connection config."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests
import json
import time

base = 'http://47.236.78.123:8100'

def get_fresh_token():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f'{base}/', timeout=60000, wait_until='domcontentloaded')
        page.wait_for_load_state('networkidle', timeout=30000)
        page.wait_for_selector('input', timeout=10000)
        inputs = page.query_selector_all('input')
        inputs[0].fill('admin')
        inputs[1].fill('DataEase@123456')
        page.query_selector('button').click()
        time.sleep(5)
        page.wait_for_load_state('networkidle', timeout=30000)
        token_raw = page.evaluate("() => localStorage.getItem('user.token')")
        token_obj = json.loads(token_raw)
        jwt = json.loads(token_obj['v'])
        browser.close()
        return jwt

token = get_fresh_token()
headers = {'x-de-token': token, 'Content-Type': 'application/json'}

sr_ds_id = 1236022373120086016

r = requests.get(f'{base}/de2api/datasource/get/{sr_ds_id}', headers=headers, timeout=30)
data = r.json().get('data', {})
print(f"Full data keys: {list(data.keys())}")
config_str = data.get('configuration', '') or data.get('configurationEncryption', '') or ''
print(f"Config type: {type(config_str)}, len: {len(str(config_str))}")
print(f"Config preview: {str(config_str)[:500]}")
if config_str:
    config = json.loads(config_str) if isinstance(config_str, str) else config_str
    print(f"Host: {config.get('host')}")
    print(f"Port: {config.get('port')}")
    print(f"Database: {config.get('dataBase')}")
    print(f"Username: {config.get('username')}")
    pwd = config.get('password', '')
    print(f"Password length: {len(pwd)}")
    print(f"Password: {pwd}")
    print(f"\nExtra params: {config.get('extraParams', '')}")
