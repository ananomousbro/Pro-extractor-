import urllib.request
import base64
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    
    key = b'E12K7l97Z7wCo3Gu'
    iv = b'mOk15J2m12qZ2tKI'
    cwkey_b64 = "I6WakWiwTfJ+g/azCL2444bdaTvT7SUzeylfzy4s/vg="
    enc = base64.b64decode(cwkey_b64)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    msg = decryptor.update(enc) + decryptor.finalize()
    print("Decrypted cwkey:", msg)
except Exception as e:
    print(e)
