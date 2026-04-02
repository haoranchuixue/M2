import requests
import json
import time
import hmac
import hashlib
import base64
import uuid

base = 'http://47.236.78.123:8100'

# Try the RSA approach from the DataEase source
# In DataEase, the dekey is used with a custom RSA implementation
# Let me try to use the JavaScript-based approach by looking at JSEncrypt

# First, let me try the login with the raw password (not encrypted)
# Maybe the encryption is optional in some versions
payloads_to_try = [
    {'name': 'admin', 'pwd': 'DataEase@123456'},
    {'name': 'admin', 'pwd': 'RGF0YUVhc2VAMTIzNDU2'},  # base64 of DataEase@123456
]

for p in payloads_to_try:
    r = requests.post(f'{base}/de2api/login/localLogin', json=p, timeout=10)
    resp = r.json()
    print(f'Payload: {p}')
    print(f'  Code: {resp.get("code")}, Msg: {resp.get("msg")}')
    if resp.get('data'):
        print(f'  Data: {str(resp["data"])[:200]}')
    print()

# Also try the API key approach - first need to check /de2api endpoints
# Look for any accessible endpoints
test_endpoints = [
    ('GET', '/de2api/sysParameter/ui'),
    ('GET', '/de2api/sysParameter/requestTimeOut'),
    ('GET', '/de2api/sysParameter/defaultLogin'),
    ('GET', '/de2api/share/proxyInfo'),
]

print("\n=== Testing public endpoints ===")
for method, endpoint in test_endpoints:
    try:
        if method == 'GET':
            r = requests.get(f'{base}{endpoint}', timeout=5)
        else:
            r = requests.post(f'{base}{endpoint}', json={}, timeout=5)
        if r.status_code != 401:
            print(f'{method} {endpoint}: Status={r.status_code}, {r.text[:200]}')
    except:
        pass

# Check DataEase version
print("\n=== Checking version ===")
version_endpoints = [
    '/de2api/sysParameter/sysEnv',
    '/de2api/about/build/version',
]
for ep in version_endpoints:
    try:
        r = requests.get(f'{base}{ep}', timeout=5)
        if r.status_code != 401:
            print(f'{ep}: {r.text[:200]}')
    except:
        pass
