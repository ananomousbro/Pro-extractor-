import time
import base64
from Crypto.Cipher import AES

def generate_cwkey():
    key = b'E12K7l97Z7wCo3Gu'
    iv = b'mOk15J2m12qZ2tKI'
    msg = f"{int(time.time()*1000)}||crwillweb@4598".encode('utf-8')
    pad = 16 - (len(msg) % 16)
    msg += bytes([pad] * pad)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    enc = cipher.encrypt(msg)
    return base64.b64encode(enc).decode('utf-8')

print(generate_cwkey())
