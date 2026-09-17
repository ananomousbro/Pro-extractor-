import requests
import json
headers = {
    "Host": "wbspec.crwilladmin.com",
    "appver": "1",
    "apptype": "web",
    "cwkey": "I6WakWiwTfJ+g/azCL2444bdaTvT7SUzeylfzy4s/vg=",
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
    "origin": "https://web.careerwill.com",
    "referer": "https://web.careerwill.com/"
}
data = {
    "deviceType": "web",
    "pwd": "test",
    "deviceModel": "ChromeCDM",
    "deviceVersion": "152.0.0.0",
    "userid": "7498987488",
    "deviceIMEI": "d1a5b3b4-d6f7-4998-8cdb-81bb1c3ed6b7-5a487141-e89a-4ad5-9d72-b031b3e80340-07046ee9-9885-4882-8b90-de6904db0dff"
}
try:
    resp = requests.post("https://wbspec.crwilladmin.com/api/v1/login", headers=headers, json=data, timeout=10)
    print(resp.status_code)
    print(resp.text)
except Exception as e:
    print(e)
