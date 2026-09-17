import base64
import time

def generate_cwkey():
    try:
        try:
            from Crypto.Cipher import AES
        except ImportError:
            from Cryptodome.Cipher import AES
        key = b'E12K7l97Z7wCo3Gu'
        iv = b'mOk15J2m12qZ2tKI'
        msg = f"{int(time.time()*1000)}||crwillweb@4598".encode('utf-8')
        pad = 16 - (len(msg) % 16)
        msg += bytes([pad] * pad)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        enc = cipher.encrypt(msg)
        return base64.b64encode(enc).decode('utf-8')
    except Exception as e:
        print(f"Error in generate_cwkey: {e}")
        return "+HwN3zs4tPU0p8BpOG5ZlXIU6MaWQmnMHXMJLLFcJ5m4kWqLXGLpsp8+2ydtILXy"

print(generate_cwkey())
