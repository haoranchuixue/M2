"""List dataset fields."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, json, time

base = 'http://47.236.78.123:8100'

def get_token():
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

token = get_token()
headers = {'x-de-token': token, 'Content-Type': 'application/json'}
dataset_id = 1236046190513098752

r = requests.post(f'{base}/de2api/datasetTree/details/{dataset_id}', headers=headers, json={}, timeout=30)
fields = r.json()['data']['allFields']
print(f'Dataset fields ({len(fields)}):')
for f in fields:
    print(f'  {f["originName"]:30s} {f["type"]:10s} group={f["groupType"]}')
