"""DataEase API helper - uses the token from Playwright login."""
import requests
import json

base = 'http://47.236.78.123:8100'

# Load token
with open('d:/Projects/m2/scripts/de_token.json', 'r') as f:
    token_data = json.load(f)

# Extract actual JWT from the wsCache format
raw = token_data['token']
token_obj = json.loads(raw) if isinstance(raw, str) else raw
jwt_token = json.loads(token_obj['v']) if isinstance(token_obj, dict) else token_obj
print(f"JWT Token: {jwt_token[:50]}...")

headers = {
    'Authorization': jwt_token,
    'Content-Type': 'application/json'
}

# 1. List data sources
print("\n=== Data Sources ===")
r = requests.post(f'{base}/de2api/datasource/list', headers=headers, json={}, timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    resp = r.json()
    print(f"Code: {resp.get('code')}")
    if resp.get('data'):
        for ds in resp['data'] if isinstance(resp['data'], list) else [resp['data']]:
            print(f"  - {json.dumps(ds, ensure_ascii=False)[:200]}")

# 2. List datasets
print("\n=== Datasets ===")
r = requests.post(f'{base}/de2api/dataset/list', headers=headers, json={}, timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    resp = r.json()
    print(f"Code: {resp.get('code')}")
    if resp.get('data'):
        data = resp['data'] if isinstance(resp['data'], list) else [resp['data']]
        for ds in data[:20]:
            print(f"  - {json.dumps(ds, ensure_ascii=False)[:200]}")

# 3. List dashboards/panels
print("\n=== Dashboards ===")
r = requests.post(f'{base}/de2api/panel/list', headers=headers, json={}, timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    resp = r.json()
    print(f"Code: {resp.get('code')}")
    if resp.get('data'):
        data = resp['data'] if isinstance(resp['data'], list) else [resp['data']]
        for d in data[:20]:
            print(f"  - {json.dumps(d, ensure_ascii=False)[:200]}")
