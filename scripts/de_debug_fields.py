"""Debug: check field properties that might contain base64-illegal chars."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, time

base = 'http://47.236.78.123:8100'
OLD_DS_ID = '1236046190513098752'

def tok():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page()
        pg.goto(base+'/', timeout=60000, wait_until='domcontentloaded')
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
r = requests.post(f'{base}/de2api/datasetTree/details/{OLD_DS_ID}', headers=h, json={}, timeout=30)
old_ds = r.json()['data']
all_fields = old_ds.get('allFields', [])

for f in all_fields:
    dn = f.get('dataeaseName', '')
    fsn = f.get('fieldShortName', '')
    on = f.get('originName', '')
    if ' ' in str(dn) or ' ' in str(fsn) or ' ' in str(on):
        print(f'SPACE in field: originName={on!r} dataeaseName={dn!r} fieldShortName={fsn!r}')
    if len(str(on)) > 30:
        print(f'LONG originName: {on[:40]!r}...')
    print(f'  {on:30s} dn={str(dn)[:30]:30s} fsn={str(fsn)[:30]:30s} id={f["id"]}')
