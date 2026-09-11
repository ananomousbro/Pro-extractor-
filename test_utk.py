import urllib.request, ssl, re, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request("https://utkarsh.com/", headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, context=ctx).read().decode("utf-8")
chunks = re.findall(r'/_next/static/chunks/[^"]+\.js', html)

found_endpoints = set()
for c in chunks:
    try:
        url = "https://utkarsh.com" + c
        js = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), context=ctx).read().decode("utf-8")
        matches = re.findall(r'["\x27\x60](https?://[a-zA-Z0-9\.\-_/]+)["\x27\x60]', js)
        for m in matches:
            if "utkarsh" in m or "api" in m:
                found_endpoints.add(m)
        api_paths = re.findall(r'["\x27\x60](/(?:api|v[0-9]|web|auth)/[a-zA-Z0-9\.\-_/]+)["\x27\x60]', js)
        for p in api_paths:
            found_endpoints.add(p)
    except Exception:
        pass

for ep in sorted(found_endpoints):
    print(ep)
