"""Find the existing 'DSP Adv Index Report' dataset and test querying it."""
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

dsp_group_id = 1236043392912330752

# List all datasets in the DSP group
r = requests.post(f'{base}/de2api/datasetTree/tree', headers=headers, json={"leafType": "dataset"}, timeout=30)
tree = r.json().get('data', [])

def find_datasets(nodes, target_name=None, depth=0):
    results = []
    for n in nodes:
        name = n.get('name', '')
        ntype = n.get('nodeType', '')
        nid = n.get('id', '')
        if ntype == 'dataset':
            results.append({'id': nid, 'name': name, 'pid': n.get('pid')})
            print(f"{'  '*depth}[DS] {name} (id={nid})")
        else:
            print(f"{'  '*depth}[folder] {name} (id={nid})")
        children = n.get('children', [])
        if children:
            results.extend(find_datasets(children, target_name, depth + 1))
    return results

print("=== All datasets ===")
all_ds = find_datasets(tree)

# Find the adv report dataset
adv_ds = [d for d in all_ds if 'adv' in d['name'].lower() or 'Adv' in d['name']]
print(f"\n=== Adv-related datasets: {len(adv_ds)} ===")
for d in adv_ds:
    print(f"  {d['name']} -> id={d['id']}")

# If found, get details and try a test query
if adv_ds:
    ds_id = adv_ds[0]['id']
    print(f"\n=== Getting details for dataset {ds_id} ===")
    r2 = requests.post(f'{base}/de2api/datasetTree/details/{ds_id}', headers=headers, json={}, timeout=30)
    if r2.json().get('code') == 0:
        ds = r2.json()['data']
        all_fields = ds.get('allFields', [])
        print(f"Dataset has {len(all_fields)} fields")
        for f in all_fields[:10]:
            print(f"  {f['originName']:30s} type={f.get('type','?'):10s} group={f.get('groupType','?')} id={f['id']}")
        if len(all_fields) > 10:
            print(f"  ... and {len(all_fields) - 10} more fields")
        
        # Find date field for filtering
        date_field = None
        for f in all_fields:
            if f['originName'] == 'report_date':
                date_field = f
                break
        
        # Pick a couple of dimension + metric fields
        dim_fields = [f for f in all_fields if f.get('groupType') == 'd'][:3]
        metric_fields = [f for f in all_fields if f.get('groupType') == 'q'][:3]
        
        print(f"\n=== Test query with date filter ===")
        print(f"Dims: {[f['originName'] for f in dim_fields]}")
        print(f"Metrics: {[f['originName'] for f in metric_fields]}")
        
        # Build xAxis + yAxis
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
                "dateFormat": f.get('dateFormat'),
                "dateFormatType": f.get('dateFormatType'),
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
                "dateFormat": f.get('dateFormat'),
                "dateFormatType": f.get('dateFormatType'),
                "sort": "none",
                "filter": [],
                "fieldShortName": f.get('fieldShortName'),
                "chartType": "table-normal",
                "summary": "sum"
            })
        
        # Build custom filter for last 3 days
        custom_filter = None
        if date_field:
            custom_filter = {
                "logic": "and",
                "items": [{
                    "type": "field",
                    "fieldId": int(date_field['id']),
                    "filterType": "logic",
                    "term": "ge",
                    "value": "2026-03-27",
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
        
        print(f"\nSending chartData/getData request...")
        r3 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=chart_payload, timeout=120)
        print(f"Status: {r3.status_code}")
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
                print(f"First 3 rows:")
                for row in rows[:3]:
                    print(f"  {row}")
            sql = data.get('sql')
            if sql:
                print(f"\nGenerated SQL:\n{sql[:1000]}")
        else:
            msg3 = resp3.get('msg', '')
            print(f"Error: {str(msg3)[:500]}")
            data = resp3.get('data', {})
            if isinstance(data, dict):
                sql = data.get('sql', '')
                if sql:
                    print(f"SQL: {sql[:500]}")
