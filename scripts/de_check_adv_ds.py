"""Check the DSP Adv Index Report dataset details and test query."""
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

ds_id = "1236079082777743360"

print(f"=== Getting dataset details for {ds_id} ===")
r = requests.post(f'{base}/de2api/datasetTree/details/{ds_id}', headers=headers, json={}, timeout=30)
resp = r.json()
print(f"Code: {resp.get('code')}")
if resp.get('code') == 0:
    ds = resp['data']
    print(f"Name: {ds.get('name')}")
    print(f"NodeType: {ds.get('nodeType')}")
    print(f"Type: {ds.get('type')}")
    all_fields = ds.get('allFields', [])
    print(f"Fields: {len(all_fields)}")
    for f in all_fields:
        print(f"  {f['originName']:35s} type={f.get('type','?'):12s} group={f.get('groupType','?'):2s} deType={f.get('deType',0)} id={f['id']}")
    
    if all_fields:
        date_field = None
        for f in all_fields:
            if f['originName'] == 'report_date':
                date_field = f
                break
        
        dim_fields = [f for f in all_fields if f.get('groupType') == 'd'][:3]
        metric_fields = [f for f in all_fields if f.get('groupType') == 'q'][:3]
        
        print(f"\n=== Test query (3 dims, 3 metrics, date >= 2026-03-28) ===")
        print(f"Dims: {[f['originName'] for f in dim_fields]}")
        print(f"Metrics: {[f['originName'] for f in metric_fields]}")
        
        x_fields = []
        for f in dim_fields:
            x_fields.append({
                "id": f['id'],
                "chartId": None,
                "datasourceId": f.get('datasourceId'),
                "datasetTableId": f.get('datasetTableId'),
                "datasetGroupId": str(ds_id),
                "originName": f['originName'],
                "name": f.get('name', f['originName']),
                "dataeaseName": f.get('dataeaseName'),
                "groupType": "d",
                "type": f['type'],
                "deType": f.get('deType', 0),
                "deExtractType": f.get('deExtractType', 0),
                "extField": f.get('extField', 0),
                "checked": True,
                "columnIndex": f.get('columnIndex', 0),
                "sort": "none",
                "filter": [],
                "fieldShortName": f.get('fieldShortName'),
                "chartType": "table-normal",
                "summary": ""
            })
        
        y_fields = []
        for f in metric_fields:
            y_fields.append({
                "id": f['id'],
                "chartId": None,
                "datasourceId": f.get('datasourceId'),
                "datasetTableId": f.get('datasetTableId'),
                "datasetGroupId": str(ds_id),
                "originName": f['originName'],
                "name": f.get('name', f['originName']),
                "dataeaseName": f.get('dataeaseName'),
                "groupType": "q",
                "type": f['type'],
                "deType": f.get('deType', 0),
                "deExtractType": f.get('deExtractType', 0),
                "extField": f.get('extField', 0),
                "checked": True,
                "columnIndex": f.get('columnIndex', 0),
                "sort": "none",
                "filter": [],
                "fieldShortName": f.get('fieldShortName'),
                "chartType": "table-normal",
                "summary": "sum"
            })
        
        custom_filter = None
        if date_field:
            custom_filter = {
                "logic": "and",
                "items": [{
                    "type": "field",
                    "fieldId": int(date_field['id']),
                    "filterType": "logic",
                    "term": "ge",
                    "value": "2026-03-28",
                    "filterTypeTime": "dateValue"
                }],
                "filterType": "logic"
            }
        
        chart_payload = {
            "type": "table-normal",
            "tableId": str(ds_id),
            "xAxis": x_fields,
            "xAxisExt": [],
            "yAxis": y_fields,
            "yAxisExt": [],
            "extStack": [],
            "extBubble": [],
            "extLabel": [],
            "extTooltip": [],
            "customFilter": custom_filter,
            "drill": False,
            "drillFields": [],
            "drillFilters": [],
            "senior": {"functionCfg": {"sliderShow": False, "sliderRange": [0, 10], "roam": True}},
            "resultCount": 1000,
            "resultMode": "custom",
            "chartExtRequest": {"user": 1, "filter": [], "drill": [], "queryFrom": "panel", "resultCount": 1000, "resultMode": "custom"}
        }
        
        print(f"\nSending chartData/getData...")
        start = time.time()
        r3 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=chart_payload, timeout=180)
        elapsed = time.time() - start
        print(f"Status: {r3.status_code} ({elapsed:.1f}s)")
        resp3 = r3.json()
        code3 = resp3.get('code', -1)
        print(f"Code: {code3}")
        if code3 == 0:
            data = resp3.get('data', {})
            table_data = data.get('data', {})
            fields_resp = table_data.get('fields', [])
            rows = table_data.get('tableRow', [])
            print(f"Fields returned: {len(fields_resp)}")
            print(f"Rows returned: {len(rows)}")
            if rows:
                print(f"First 5 rows:")
                for row in rows[:5]:
                    print(f"  {json.dumps(row, ensure_ascii=False)[:200]}")
            sql = data.get('sql')
            if sql:
                print(f"\nGenerated SQL:\n{sql[:1500]}")
        else:
            msg3 = resp3.get('msg', '')
            print(f"Error: {str(msg3)[:500]}")
            data = resp3.get('data', {})
            if isinstance(data, dict):
                sql = data.get('sql', '')
                if sql:
                    print(f"SQL: {sql[:500]}")
else:
    print(f"Error: {resp.get('msg', '')}")
