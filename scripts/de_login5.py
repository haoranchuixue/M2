import requests
import re

base = 'http://47.236.78.123:8100'

# Get the main JS
r = requests.get(f'{base}/js/index-0.0.0-dataease.js', timeout=10)
# Find all chunk references
chunks = re.findall(r'"([^"]*\.js)"', r.text)
print(f"Total chunks: {len(chunks)}")

# Check each chunk for encrypt/RSA/login patterns
for chunk in chunks:
    url = f'{base}/{chunk.lstrip("./")}'
    try:
        r2 = requests.get(url, timeout=5)
        js = r2.text
        if any(kw in js.lower() for kw in ['encrypt', 'rsa', 'locallogin', 'jsencrypt']):
            print(f"\n=== FOUND in {chunk} (size={len(js)}) ===")
            for pat in ['encrypt', 'RSA', 'JSEncrypt', 'localLogin', 'rsaEncrypt', 'publicKey']:
                for m in re.finditer(pat, js, re.IGNORECASE):
                    start = max(0, m.start() - 150)
                    end = min(len(js), m.end() + 150)
                    print(f"  [{pat} at {m.start()}]: ...{js[start:end]}...")
                    break  # just first match per pattern per chunk
    except:
        pass
