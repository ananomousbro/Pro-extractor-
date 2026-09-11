import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request("https://utkarsh.com/", headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, context=ctx).read().decode("utf-8")
chunks = re.findall(r'/_next/static/chunks/[^"]+\.js', html)

for c in chunks:
    try:
        url = "https://utkarsh.com" + c
        js = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), context=ctx).read().decode("utf-8")
        if "services.utkarsh.com" in js:
            print("Found in", c)
            matches = re.findall(r'["\x27\x60](https?://services\.utkarsh\.com/api/[^"\x27\x60 ]+)["\x27\x60]', js)
            for m in set(matches):
                print("  ->", m)
        if "login" in js.lower() and ("mobile" in js.lower() or "password" in js.lower() or "otp" in js.lower()):
            matches = re.findall(r'["\x27\x60](/(?:api|v[0-9]|web|user|auth)/[^"\x27\x60 ]+)["\x27\x60]', js)
            for m in set(matches):
                if any(k in m.lower() for k in ["login", "auth", "user", "otp", "verify"]):
                    print("  auth path ->", m)
    except Exception:
        pass
