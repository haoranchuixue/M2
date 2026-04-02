import requests
import re

# Download the main JS bundle
r = requests.get('http://47.236.78.123:8100/js/index-0.0.0-dataease.js', timeout=30)
js = r.text
print(f"JS file size: {len(js)} bytes")

# Find all chunk references
chunks = re.findall(r'["\']([^"\']*\.js)["\']', js)
print(f"Referenced chunks: {len(chunks)}")
for c in chunks[:30]:
    print(f"  {c}")

# Also find import patterns
imports = re.findall(r'import\("([^"]+)"\)', js)
print(f"\nDynamic imports: {len(imports)}")
for i in imports[:20]:
    print(f"  {i}")

# Find all assets paths
assets = re.findall(r'assets/[a-zA-Z0-9_-]+\.js', js)
print(f"\nAsset JS files: {len(set(assets))}")
for a in sorted(set(assets))[:30]:
    print(f"  {a}")

# Check for login-related strings
login_refs = re.findall(r'[a-zA-Z_]*[Ll]ogin[a-zA-Z_]*', js)
print(f"\nLogin refs: {set(login_refs)}")

# Check for RSA
rsa_refs = re.findall(r'[a-zA-Z_]*[Rr][Ss][Aa][a-zA-Z_]*', js)
print(f"\nRSA refs: {set(rsa_refs)}")

# Look for encrypt
enc_refs = re.findall(r'[a-zA-Z_]*[Ee]ncrypt[a-zA-Z_]*', js)
print(f"\nEncrypt refs: {set(enc_refs)}")
