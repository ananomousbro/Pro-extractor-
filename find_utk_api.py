import urllib.request, ssl, re, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request("https://utkarsh.com/", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
html = urllib.request.urlopen(req, context=ctx).read().decode("utf-8")
chunks = re.findall(r'/_next/static/chunks/[^"]+\.js', html)

found = set()
for c in chunks:
    try:
        url = "https://utkarsh.com" + c
        js = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), context=ctx).read().decode("utf-8")
        matches = re.findall(r'https?://services\.utkarsh\.com[^\s"\'`]+', js)
        for m in matches:
            found.add(m)
        apis = re.findall(r'["\'](/api/v[0-9]/[^"\'`]+)["\']', js)
        for a in apis:
            found.add(a)
    except Exception:
        pass

print("Total endpoints found:", len(found))
for x in sorted(found):
    print(x)
