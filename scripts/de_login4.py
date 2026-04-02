import requests
import re

base = 'http://47.236.78.123:8100'

# Check the app chunk for login logic
chunks_to_check = [
    '/assets/chunk/app-0.0.0-dataease.js',
    '/assets/chunk/common-0.0.0-dataease.js',
    '/assets/chunk/index-0.0.0-dataease.js',
]

for chunk in chunks_to_check:
    url = f'{base}{chunk}'
    r = requests.get(url, timeout=10)
    js = r.text
    
    has_login = 'login' in js.lower() or 'Login' in js
    has_rsa = 'rsa' in js.lower() or 'RSA' in js
    has_encrypt = 'encrypt' in js.lower()
    has_dekey = 'dekey' in js.lower()
    
    print(f"{chunk}: size={len(js)}, login={has_login}, rsa={has_rsa}, encrypt={has_encrypt}, dekey={has_dekey}")
    
    if has_encrypt or has_rsa or has_dekey:
        # Find the relevant sections
        for pat in ['dekey', 'encrypt', 'RSA', 'publicKey', 'localLogin']:
            for m in re.finditer(pat, js, re.IGNORECASE):
                start = max(0, m.start() - 200)
                end = min(len(js), m.end() + 200)
                print(f"\n  --- {pat} at {m.start()} ---")
                print(f"  {js[start:end]}")
