"""DataEase API helper - try different header formats."""
import requests
import json

base = 'http://47.236.78.123:8100'

with open('d:/Projects/m2/scripts/de_token.json', 'r') as f:
    token_data = json.load(f)

raw = token_data['token']
token_obj = json.loads(raw) if isinstance(raw, str) else raw
jwt_token = json.loads(token_obj['v']) if isinstance(token_obj, dict) else token_obj
print(f"JWT Token: {jwt_token[:80]}...")

# Try different header combinations
header_combos = [
    {'Authorization': f'Bearer {jwt_token}'},
    {'Authorization': jwt_token},
    {'X-DE-TOKEN': jwt_token},
    {'DE-TOKEN': jwt_token},
    {'token': jwt_token},
    {'Authorization': f'Bearer {jwt_token}', 'X-DE-TOKEN': jwt_token},
]

test_url = f'{base}/de2api/datasource/list'

for i, h in enumerate(header_combos):
    h['Content-Type'] = 'application/json'
    r = requests.post(test_url, headers=h, json={}, timeout=5)
    resp_text = r.text[:200]
    print(f"\nCombo {i}: {list(h.keys())} -> Status {r.status_code}: {resp_text}")

# Also try GET method
print("\n\n=== Trying GET method ===")
for url in [f'{base}/de2api/datasource/list', f'{base}/de2api/datasource/query']:
    for h in [{'Authorization': f'Bearer {jwt_token}'}, {'X-DE-TOKEN': jwt_token}]:
        h['Content-Type'] = 'application/json'
        r = requests.get(url, headers=h, timeout=5)
        print(f"GET {url.split('/')[-1]}: {list(h.keys())} -> {r.status_code}: {r.text[:200]}")
