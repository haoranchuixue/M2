"""Check field types in the new dataset."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, time

base = 'http://47.236.78.123:8100'
DS_ID = '1236796318811295744'

def tok():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page()
        pg.goto(base + '/', timeout=60000, wait_until='domcontentloaded')
        pg.wait_for_load_state('networkidle', timeout=30000)
        pg.wait_for_selector('input', timeout=10000)
        ins = pg.query_selector_all('input')
        ins[0].fill('admin')
        ins[1].fill('DataEase@123456')
        pg.query_selector('button').click()
        time.sleep(5)
        pg.wait_for_load_state('networkidle', timeout=30000)
        tr = pg.evaluate('() => localStorage.getItem("user.token")')
        jwt = json.loads(json.loads(tr)['v'])
        b.close()
        return jwt

h = {'x-de-token': tok(), 'Content-Type': 'application/json'}

r = requests.post(f'{base}/de2api/datasetTree/details/{DS_ID}', headers=h, json={}, timeout=30)
fields = r.json()['data']['allFields']
for f in fields:
    print(f'{f["originName"]:25s} type={f.get("type"):10s} deType={f.get("deType")} groupType={f.get("groupType")} id={f["id"]}')
