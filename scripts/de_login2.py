import requests
import re
import json

# Download the main JS bundle
print("Downloading JS bundle...")
r = requests.get('http://47.236.78.123:8100/js/index-0.0.0-dataease.js', timeout=30)
print(f"JS file size: {len(r.text)} bytes")

# Search for login-related code
js = r.text

# Find RSA encryption patterns
patterns = [
    r'dekey',
    r'RSAKey',
    r'JSEncrypt',
    r'encrypt',
    r'localLogin',
    r'setPublicKey',
    r'publicKey',
]

for pat in patterns:
    matches = [(m.start(), m.end()) for m in re.finditer(pat, js, re.IGNORECASE)]
    if matches:
        print(f"\n=== Pattern '{pat}' found {len(matches)} times ===")
        for start, end in matches[:3]:
            context_start = max(0, start - 100)
            context_end = min(len(js), end + 100)
            snippet = js[context_start:context_end]
            print(f"  ...{snippet}...")
