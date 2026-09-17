import re

import requests 
import datetime, pytz, re, aiofiles, subprocess, os, base64, io, asyncio, time
import json, tqdm, urllib.parse
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from base64 import b64decode
from pyrogram import filters
from Extractor import app
from config import CHANNEL_ID, THUMB_URL, TXT_LOGO_URL
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init
from termcolor import colored
from pyrogram.errors import FloodWait, RPCError
from pyrogram.session import Session
from contextlib import asynccontextmanager
import aiohttp
import logging
from datetime import timedelta
from Extractor.core.utils import forward_to_log

# Initialize colorama for Windows compatibility
init(autoreset=True)

appname = "Utkarsh"
txt_dump = CHANNEL_ID
MAX_CONCURRENT_REQUESTS = 1000  # Increased concurrency for faster processing
MAX_RETRIES = 15  # For request retry logic
TIMEOUT = 90  # Increased timeout for large batches
UPDATE_DELAY = 5  # Delay between message updates
SESSION_TIMEOUT = 200  # Session timeout in seconds
EDIT_LOCK = asyncio.Lock()
MAX_WORKERS = 5000  # Increased workers for better performance
UPDATE_INTERVAL = 15  # Update progress message every 15 seconds
CHECKPOINT_FILE = "batch_checkpoint.json"

class SessionManager:
    def __init__(self, app):
        self.app = app
        self.lock = asyncio.Lock()
        self._session = None
        self.last_used = 0
        
    async def get_session(self):
        async with self.lock:
            current_time = time.time()
            if self._session is None or (current_time - self.last_used) > SESSION_TIMEOUT:
                if self._session:
                    await self._session.stop()
                self._session = await self.app.storage.conn.get_session()
                self.last_used = current_time
            return self._session
            
    async def release(self):
        async with self.lock:
            if self._session:
                try:
                    await self._session.stop()
                except Exception:
                    pass
                finally:
                    self._session = None

@asynccontextmanager
async def managed_edit(message, session_manager):
    """Context manager for safe message editing with session management"""
    try:
        await session_manager.get_session()
        yield
    except FloodWait as e:
        print(colored(f"⚠️ FloodWait: Waiting for {e.value} seconds", "yellow"))
        await asyncio.sleep(e.value)
    except Exception as e:
        print(colored(f"❌ Error in message edit: {str(e)}", "red"))
    finally:
        await session_manager.release()

async def safe_edit_message(message, text):
    """Safely edit a message with retry logic and delay"""
    async with EDIT_LOCK:  # Use a lock to prevent concurrent edits
        for attempt in range(MAX_RETRIES):
            try:
                await asyncio.sleep(UPDATE_DELAY)  # Add delay between edits
                await message.edit(text)
                return True
            except FloodWait as e:
                print(colored(f"⚠️ FloodWait: Waiting for {e.value} seconds", "yellow"))
                await asyncio.sleep(e.value)
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    print(colored(f"❌ Failed to edit message after {MAX_RETRIES} attempts: {e}", "red"))
                    return False
                await asyncio.sleep(UPDATE_DELAY * 2)
        return False

def decrypt(enc):
    enc = b64decode(enc)
    Key = '%!$!%_$&!%F)&^!^'.encode('utf-8') 
    iv =  '#*y*#2yJ*#$wJv*v'.encode('utf-8') 
    cipher = AES.new(Key, AES.MODE_CBC, iv)
    plaintext =  unpad(cipher.decrypt(enc), AES.block_size)
    b = plaintext.decode('utf-8')
    return b

def transform_utk_key(base_str, salt):
    t = list(base_str)
    res = ""
    for ch in salt:
        if ch.isdigit():
            r = int(ch)
            if 0 <= r < len(t):
                res += t[r]
    return res

def pad16_utk(st):
    if len(st) < 16:
        return st.ljust(16, "0")
    elif len(st) > 16:
        return st[:16]
    return st

def encrypt_utk_web(plaintext, salt=None):
    a = "%!F*&^$)_*%3f&B+"
    s = "#*$DJvyw2w%!_-$@"
    t = transform_utk_key(a, salt) if salt else a
    l = transform_utk_key(s, salt) if salt else s
    kd = pad16_utk(t).encode("utf-8")
    kc = pad16_utk(l).encode("utf-8")
    cipher = AES.new(kd, AES.MODE_CBC, kc)
    ct = cipher.encrypt(pad(plaintext.encode("utf-8"), AES.block_size))
    ct_b64 = base64.b64encode(ct).decode("utf-8")
    salt_b64 = base64.b64encode((salt or "").encode("utf-8")).decode("utf-8")
    return f"{ct_b64}:{salt_b64}"

def decrypt_utk_web(ciphertext, salt=None):
    if not ciphertext:
        return None
    a = "%!F*&^$)_*%3f&B+"
    s = "#*$DJvyw2w%!_-$@"
    t = transform_utk_key(a, salt) if salt else a
    l = transform_utk_key(s, salt) if salt else s
    kd = pad16_utk(t).encode("utf-8")
    kc = pad16_utk(l).encode("utf-8")
    u = ciphertext.split(":")[0]
    raw = base64.b64decode(u)
    cipher = AES.new(kd, AES.MODE_CBC, kc)
    pt = unpad(cipher.decrypt(raw), AES.block_size).decode("utf-8")
    return pt

def get_utk_guest_jwt():
    """Fetch guest JWT token required by application.utkarshapp.com API"""
    try:
        r = requests.get("https://utkarsh.com/api/guest-login", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) utkarsh_windows_64/0.3.6 Chrome/108.0.5359.215 Electron/22.3.24 Safari/537.36"}, timeout=10)
        data = r.json()
        return data.get("jwt", "")
    except Exception as e:
        print(colored(f"⚠️ Guest JWT fetch error: {e}", "yellow"))
        return ""

def send_utk_otp(mobile):
    """Send login OTP to mobile number via Utkarsh API"""
    try:
        guest_jwt = get_utk_guest_jwt()
        key_seed = "0016108641027451"
        payload = json.dumps({
            "mobile": str(mobile),
            "is_social": 0,
            "#otp": "",
            "is_registration": 0,
            "resend": 0,
            "device_id": "testingapi",
            "device_token": "testingpostmanrequest"
        })
        enc_body = encrypt_utk_web(payload, key_seed)
        headers = {
            "lang": "1",
            "version": "1",
            "Devicetype": "4",
            "Authorization": "Bearer 01*#NerglnwwebOI)30@I*Dm'@@",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) utkarsh_windows_64/0.3.6 Chrome/108.0.5359.215 Electron/22.3.24 Safari/537.36",
            "Userid": "0"
        }
        if guest_jwt:
            headers["Jwt"] = guest_jwt
        res = requests.post(
            "https://application.utkarshapp.com/data_model/users/login_with_otp",
            data=json.dumps(enc_body),
            headers=headers,
            timeout=15
        )
        resp_text = res.text.strip().strip('"')
        dec_json_str = decrypt_utk_web(resp_text, key_seed)
        if dec_json_str:
            data = json.loads(dec_json_str)
            status = data.get("status", False)
            msg = data.get("message", "Failed to send OTP")
            return status, msg, guest_jwt
        return False, "Failed to decrypt response from Utkarsh", guest_jwt
    except Exception as e:
        return False, str(e), ""

def verify_utk_otp(mobile, otp, guest_jwt, sess):
    """Verify login OTP and automatically establish session on online.utkarsh.com"""
    try:
        key_seed = "0016108641027451"
        payload = json.dumps({
            "mobile": str(mobile),
            "is_social": 0,
            "otp": str(otp),
            "is_registration": 0,
            "resend": 0,
            "cta_action": "",
            "device_id": "testingapi",
            "device_token": "testingpostmanrequest"
        })
        enc_body = encrypt_utk_web(payload, key_seed)
        headers = {
            "lang": "1",
            "version": "1",
            "Devicetype": "4",
            "Authorization": "Bearer 01*#NerglnwwebOI)30@I*Dm'@@",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) utkarsh_windows_64/0.3.6 Chrome/108.0.5359.215 Electron/22.3.24 Safari/537.36",
            "Userid": "0"
        }
        if guest_jwt:
            headers["Jwt"] = guest_jwt
        res = requests.post(
            "https://application.utkarshapp.com/data_model/users/login_with_otp",
            data=json.dumps(enc_body),
            headers=headers,
            timeout=15
        )
        resp_text = res.text.strip().strip('"')
        dec_json_str = decrypt_utk_web(resp_text, key_seed)
        if not dec_json_str:
            return False, "Failed to decrypt OTP verification response", None
        
        data = json.loads(dec_json_str)
        status = data.get("status", False)
        msg = data.get("message", "OTP verification failed")
        if not status:
            return False, msg, None

        user_data = data.get("data", {})
        jwt_token = user_data.get("jwt", "") if isinstance(user_data, dict) else ""
        if not jwt_token:
            return False, "No JWT token in response", None

        # Auto-login to online.utkarsh.com using the new JWT to obtain session cookies
        enc_obj = json.dumps({"jwt": jwt_token, "redirect_url": "https://online.utkarsh.com/web/Study/index"})
        enc_web_token = encrypt_utk_web(enc_obj, "0161086410274515")
        b64_web = base64.b64encode(enc_web_token.encode()).decode()
        target_url = f"https://online.utkarsh.com/web/web_panel_ini/auto_login_web?web_token={b64_web}"
        sess.get(target_url, headers={"Referer": "https://utkarsh.com/"}, timeout=TIMEOUT, allow_redirects=True)
        return True, "Login successful", jwt_token
    except Exception as e:
        return False, str(e), None

@app.on_message(filters.command(["utkarsh", "utk", "utk_dl"]))  # Added more handlers
async def handle_utk_logic(app, m):
    session_manager = SessionManager(app)
    start_time = time.time()
    editable = await m.reply_text(
        "🔹 <b>UTK EXTRACTOR PRO</b> 🔹\n\n"
        "Send your login credentials or token in any format:\n\n"
        "1️⃣ <b>Mobile Number Only (OTP Login):</b>\n"
        "   <code>9876543210</code> (10-digit number)\n"
        "2️⃣ <b>ID & Password:</b>\n"
        "   <code>Mobile*Password</code>\n"
        "3️⃣ <b>Auto-Login URL / Web Token / JWT:</b>\n"
        "   <code>https://online.utkarsh.com/web/web_panel_ini/auto_login_web?web_token=...</code>\n"
        "4️⃣ <b>Cookies:</b>\n"
        "   <code>ci_session=...; csrf_name=...</code>"
    )
    # After getting user response
    input1 = await app.listen(chat_id=m.chat.id)
    await forward_to_log(input1, "Utkarsh Extractor")

    raw_text = input1.text.strip()
    await input1.delete()
    
    print(colored("🔄 Attempting login to Utkarsh...", "cyan"))
    await safe_edit_message(editable, "🔄 <b>Connecting to Utkarsh servers...</b>")
    
    sess = requests.Session()
    default_headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) utkarsh_windows_64/0.3.6 Chrome/108.0.5359.215 Electron/22.3.24 Safari/537.36',
        'origin': 'https://online.utkarsh.com',
        'referer': 'https://online.utkarsh.com/web/Study/index'
    }
    sess.headers.update(default_headers)
    
    token = ""
    logged_in = False

    # Check for mobile-only login (10 digits or with +91)
    clean_digits = re.sub(r'[\s\-\+]', '', raw_text)
    if clean_digits.startswith('91') and len(clean_digits) == 12:
        clean_digits = clean_digits[2:]
    
    # 1. Handle Mobile Number Only (OTP Flow)
    if clean_digits.isdigit() and len(clean_digits) == 10 and '*' not in raw_text and '=' not in raw_text:
        mobile_num = clean_digits
        print(colored(f"📱 Detected mobile-only login request for {mobile_num}", "cyan"))
        await safe_edit_message(editable, f"🔄 <b>Sending OTP to {mobile_num}... Please wait!</b>")
        
        otp_sent, otp_msg, guest_jwt = send_utk_otp(mobile_num)
        if not otp_sent:
            await safe_edit_message(editable, f"❌ <b>Failed to send OTP:</b> {otp_msg}\n\nPlease check your mobile number or try ID*Password.")
            print(colored(f"❌ Failed to send OTP: {otp_msg}", "red"))
            return
            
        await safe_edit_message(
            editable,
            f"✅ <b>OTP Sent Successfully!</b>\n\n"
            f"📱 Mobile: <code>{mobile_num}</code>\n"
            f"📬 Please check your SMS and send the 6-digit OTP below:"
        )
        
        otp_input = await app.listen(chat_id=m.chat.id)
        await forward_to_log(otp_input, "Utkarsh Extractor OTP")
        entered_otp = otp_input.text.strip()
        await otp_input.delete()
        
        await safe_edit_message(editable, "🔄 <b>Verifying OTP & logging in... Please wait!</b>")
        v_ok, v_msg, jwt_token = verify_utk_otp(mobile_num, entered_otp, guest_jwt, sess)
        
        if v_ok:
            token = sess.cookies.get("csrf_name", "")
            logged_in = True
            print(colored("✅ OTP login successful!", "green"))
            await safe_edit_message(
                editable,
                f"✅ <b>Login Successful via OTP!</b>\n\n"
                f"🔑 <b>Token:</b> <code>{jwt_token}</code>\n\n"
                f"🔄 <i>Fetching your enrolled courses...</i>"
            )
        else:
            await safe_edit_message(editable, f"❌ <b>Login Failed:</b> {v_msg}\n\nPlease try again with <code>/utk</code>.")
            print(colored(f"❌ OTP verification failed: {v_msg}", "red"))
            return

    # 2. Check if user provided Auto-Login URL or Web Token or JWT
    elif "auto_login_web" in raw_text or "web_token=" in raw_text or raw_text.startswith("ey") or (len(raw_text) > 100 and "*" not in raw_text and "=" in raw_text):
        try:
            target_url = ""
            if raw_text.startswith("http"):
                target_url = raw_text
            elif "web_token=" in raw_text:
                target_url = f"https://online.utkarsh.com/web/web_panel_ini/auto_login_web?{raw_text}"
            elif raw_text.startswith("ey"):
                # Encrypt JWT for auto_login_web
                enc_obj = json.dumps({"jwt": raw_text, "redirect_url": "https://online.utkarsh.com/web/Study/index"})
                enc_web_token = encrypt_utk_web(enc_obj, "0161086410274515")
                b64_web = base64.b64encode(enc_web_token.encode()).decode()
                target_url = f"https://online.utkarsh.com/web/web_panel_ini/auto_login_web?web_token={b64_web}"
            else:
                # Raw base64 web token
                target_url = f"https://online.utkarsh.com/web/web_panel_ini/auto_login_web?web_token={raw_text}"
            
            print(colored(f"🔗 Calling Utkarsh auto-login endpoint...", "cyan"))
            r_auto = sess.get(target_url, headers={"Referer": "https://utkarsh.com/"}, timeout=TIMEOUT, allow_redirects=True)
            token = sess.cookies.get("csrf_name", "")
            if token:
                logged_in = True
                print(colored("✅ Authenticated via Utkarsh web token!", "green"))
                await safe_edit_message(editable, "✅ <b>Authenticated successfully via Web Token!</b>")
        except Exception as e:
            print(colored(f"⚠️ Web token login error: {e}", "yellow"))

    # 2. Check if user provided cookies directly
    elif "ci_session=" in raw_text or "csrf_name=" in raw_text:
        try:
            for part in raw_text.split(";"):
                part = part.strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    sess.cookies.set(k.strip(), v.strip(), domain="online.utkarsh.com")
            token = sess.cookies.get("csrf_name", "")
            if token and sess.cookies.get("ci_session"):
                logged_in = True
                print(colored("✅ Session cookies set directly!", "green"))
                await safe_edit_message(editable, "✅ <b>Authenticated via Session Cookies!</b>")
        except Exception as e:
            print(colored(f"⚠️ Cookie parsing error: {e}", "yellow"))

    # 3. Handle ID*Password
    elif '*' in raw_text:
        # Fetch fresh CSRF token and ci_session from online.utkarsh.com
        for attempt in range(MAX_RETRIES):
            try:
                init_res = sess.get('https://online.utkarsh.com/', timeout=TIMEOUT)
                token = sess.cookies.get('csrf_name', '')
                if not token:
                    # Fallback pattern if cookie name varies
                    token = sess.cookies.get('csrf_cookie_name', '')
                if token:
                    print(colored(f"✅ Dynamic token obtained from Utkarsh", "green"))
                    break
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2)
                    continue
                else:
                    print(colored(f"❌ Failed to get initial cookies: {e}", "red"))
        
        if not token:
            await safe_edit_message(editable, "❌ Failed to connect to Utkarsh servers. Please try again later.")
            return

        ids, ps = raw_text.split("*", 1)
        data = f"csrf_name={token}&mobile={ids}&url=0&password={ps}&submit=LogIn&device_token=null"
        
        try:
            log_res = sess.post('https://online.utkarsh.com/web/Auth/login', data=data, timeout=TIMEOUT)
            log_json = log_res.json()
            if "response" in log_json:
                log_response = log_json["response"].replace('MDE2MTA4NjQxMDI3NDUxNQ==', '==').replace(':', '==')
                dec_log = decrypt(log_response)
                dec_logs = json.loads(dec_log)
                error_message = dec_logs.get("message", "Login failed")
                status = dec_logs.get('status', False)
            else:
                status = log_json.get('status', False)
                error_message = log_json.get('message', 'Login failed')
            
            if status:
                token = sess.cookies.get("csrf_name", token)
                logged_in = True
                await safe_edit_message(editable, "✅ <b>Authentication successful!</b>")
                print(colored("✅ Login successful!", "green"))
            else:
                await safe_edit_message(editable, f'❌ Login Failed - {error_message}')
                print(colored(f"❌ Login failed: {error_message}", "red"))
                return
        except Exception as e:
            await safe_edit_message(editable, f'❌ Error during login: {str(e)}')
            print(colored(f"❌ Exception during login: {e}", "red"))
            return
    else:
        await safe_edit_message(editable, "❌ <b>Invalid format!</b>\n\nPlease send <code>Mobile*Password</code> or Auto-Login URL / JWT / Cookies.")
        return

    if not logged_in:
        await safe_edit_message(editable, "❌ <b>Authentication failed.</b> Please check your credentials or token.")
        return

    # Prepare cookies header for downstream requests
    token = sess.cookies.get("csrf_name", token)
    cookie_str = "; ".join([f"{c.name}={c.value}" for c in sess.cookies])
    headers = default_headers.copy()
    headers['cookie'] = cookie_str

    # Fetch course data with better error handling
    try:
        data2 = f"type=Batch&csrf_name={token}&sort=0"
        course_post = sess.post('https://online.utkarsh.com/web/Profile/my_course', headers=headers, data=data2, timeout=TIMEOUT)
        
        try:
            c_json = course_post.json()
            if "response" in c_json:
                res2 = c_json["response"].replace('MDE2MTA4NjQxMDI3NDUxNQ==', '==').replace(':', '==')
                decrypted_res = decrypt(res2)
                dc = json.loads(decrypted_res)
            else:
                dc = c_json
        except Exception as e:
            print(colored(f"⚠️ Non-JSON or encrypted response parsing: {e}", "yellow"))
            dc = {}

        dataxxx = dc.get('data', {})
        if isinstance(dataxxx, dict):
            bdetail = dataxxx.get("data", [])
        elif isinstance(dataxxx, list):
            bdetail = dataxxx
        else:
            bdetail = []
        
        if not bdetail:
            await safe_edit_message(editable, "❌ No courses found in your account.")
            print(colored("⚠️ No courses found in user account", "yellow"))
            return
            
        cool = ""
        FFF = "🔸 <b>BATCH INFORMATION</b> 🔸"
        Batch_ids = ''
        
        print(colored(f"📚 Found {len(bdetail)} courses:", "cyan"))
        for item in bdetail:
            id = item.get("id")
            batch = item.get("title")
            price = item.get("mrp")
            aa = f"<code>{id}</code> - <b>{batch}</b> 💰 ₹{price}\n\n"
            print(colored(f"  • {batch} (ID: {id}) - ₹{price}", "white"))
            if len(f'{cool}{aa}') > 4096:
                cool = ""
            cool += aa
            Batch_ids += str(id) + '&'
        Batch_ids = Batch_ids.rstrip('&')
        
        login_msg = f'<b>✅ {appname} Login Successful</b>\n'    
        login_msg += f'\n<b>🆔 Credentials:</b> <code>{raw_text}</code>\n\n'
        login_msg += f'\n\n<b>📚 Available Batches</b>\n\n{cool}'    
        
        # Send login info to log channel
        copiable = await app.send_message(txt_dump, login_msg)
        
        # Send formatted batch info to user
        await safe_edit_message(editable, f'{FFF}\n\n{cool}')
    
        # Ask for batch ID selection
        editable1 = await m.reply_text(
            f"<b>📥 Send the Batch ID to download</b>\n\n"
            f"<b>💡 For ALL batches:</b> <code>{Batch_ids}</code>\n\n"
            f"<i>Supports multiple IDs separated by '&'</i>"
        )
        
        user_id = int(m.chat.id)
        input2 = await app.listen(chat_id=m.chat.id)
        await input2.delete()
        await editable.delete()
        await editable1.delete()
        
        # Process batch ID selection
        if "&" in input2.text:
            batch_ids = input2.text.split('&')
        else:
            batch_ids = [input2.text]

        opt_msg = await m.reply_text(
            "**Choose extraction type:**\n\n"
            "1️⃣ 1 — 📦 **Full Batch**\n"
            "2️⃣ 2 — 📅 **Today's Class**"
        )
        opt_input = await app.listen(chat_id=m.chat.id)
        today_only = (opt_input.text.strip() == "2")
        await opt_input.delete()
        await opt_msg.delete()

        # Process each selected batch
        for batch_id in batch_ids:
            batch_id = batch_id.strip()  # Clean input
            start_time = datetime.datetime.now()
            progress_msg = await m.reply_text(f"⏳ <b>Processing batch ID:</b> <code>{batch_id}</code>...")
            
            # Get batch name
            bname = next((x['title'] for x in bdetail if str(x['id']) == batch_id), None)
            if not bname:
                await safe_edit_message(progress_msg, f"❌ Batch ID <code>{batch_id}</code> not found!")
                continue
                
            print(colored(f"\n📦 Processing batch: {bname} (ID: {batch_id})", "cyan"))
                
            # Fetch subject data
            try:
                data4 = {
                    'tile_input': f'{{"course_id": {batch_id},"revert_api":"1#0#0#1","parent_id":0,"tile_id":"0","layer":1,"type":"course_combo"}}',
                    'csrf_name': token
                }
                Key = '%!$!%_$&!%F)&^!^'.encode('utf-8') 
                iv = '#*y*#2yJ*#$wJv*v'.encode('utf-8')   
                cipher = AES.new(Key, AES.MODE_CBC, iv)
                padded_data = pad(data4['tile_input'].encode(), AES.block_size)
                encrypted_data = cipher.encrypt(padded_data)
                encoded_data = base64.b64encode(encrypted_data).decode()
                data4['tile_input'] = encoded_data
                
                res4 = requests.post("https://online.utkarsh.com/web/Course/tiles_data", headers=headers, data=data4, timeout=TIMEOUT).json()["response"].replace('MDE2MTA4NjQxMDI3NDUxNQ==','==').replace(':', '==')
                res4_dec = decrypt(res4)
                res4_json = json.loads(res4_dec)
                subject = res4_json.get("data", [])
                
                if not subject:
                    await safe_edit_message(progress_msg, f"❌ No subjects found in batch <code>{batch_id}</code>")
                    continue
                    
                subjID = "&".join([id["id"] for id in subject])
                print(colored(f"📚 Found {len(subject)} subjects", "cyan"))
                
                subject_ids = subjID.split('&')
                
                # Process subjects with new method
                all_urls = await process_batch_subjects(app, subject_ids, subject, batch_id, headers, token, progress_msg, bname)
                
                if today_only and all_urls:
                    today_ist = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).date()
                    t_patterns = [
                        today_ist.strftime('%d-%m-%Y'),
                        today_ist.strftime('%d/%m/%Y'),
                        today_ist.strftime('%Y-%m-%d'),
                        today_ist.strftime('%d %b %Y'),
                        today_ist.strftime('%d %B %Y')
                    ]
                    all_urls = [u for u in all_urls if any(p in u for p in t_patterns)]

                if all_urls:
                    print(colored(f"✅ Successfully extracted {len(all_urls)} URLs from batch {bname}", "green"))
                    await login(app, user_id, m, all_urls, start_time, bname, batch_id, progress_msg, app_name="Utkarsh")
                else:
                    if today_only:
                        await safe_edit_message(progress_msg, "❌ **आज इस बैच में कोई भी क्लास नहीं हुई है या आज का कोई लिंक उपलब्ध नहीं है।**")
                    else:
                        await safe_edit_message(progress_msg, f"⚠️ No content URLs found in batch <code>{bname}</code>")
            except Exception as e:
                print(colored(f"❌ Error processing batch {batch_id}: {e}", "red"))
                await safe_edit_message(progress_msg, f"❌ Error processing batch: {str(e)}")
        
        # Logout after processing all batches
        try:
            logout = requests.get("https://online.utkarsh.com/web/Auth/logout", headers=headers, timeout=TIMEOUT)
            if logout.status_code == 200:
                print(colored("✅ Logout successful", "green"))
                execution_time = time.time() - start_time
                print(colored(f"⏱️ Total execution time: {execution_time:.2f} seconds", "cyan"))
        except Exception as e:
            print(colored("⚠️ Failed to logout properly", "yellow"))
            
    except Exception as e:
        print(colored(f"❌ Error fetching courses: {e}", "red"))
        await safe_edit_message(editable, f"❌ Error fetching your courses: {str(e)}")
        return
    finally:
        await session_manager.release()

async def update_progress_safely(progress_msg, text, last_update_time, min_interval=UPDATE_INTERVAL):
    """Update progress message with rate limiting"""
    current_time = time.time()
    if current_time - last_update_time >= min_interval:
        try:
            await progress_msg.edit(text)
            return current_time
        except Exception as e:
            print(colored(f"Progress update skipped: {e}", "yellow"))
    return last_update_time

async def process_single_subject(app, subject_id, subject_list, batch_id, headers, token, progress_msg, current_subject, total_subjects):
    """Process a single subject with stable progress updates"""
    topicName = next((x['title'] for x in subject_list if str(x['id']) == subject_id), "Unknown Topic")
    start_time = time.time()
    last_update_time = 0
    
    # Initial progress update
    progress_text = (
        f"🔄 <b>Processing Large Batch</b>\n"
        f"├─ Subject: {current_subject}/{total_subjects}\n"
        f"└─ Current: <code>{topicName}</code>"
    )
    last_update_time = await update_progress_safely(progress_msg, progress_text, last_update_time, 5)
    
    try:
        # Save checkpoint
        checkpoint_data = {
            "subject_id": subject_id,
            "current_subject": current_subject,
            "total_subjects": total_subjects,
            "batch_id": batch_id,
            "subject_name": topicName
        }
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(checkpoint_data, f)
        
        # Get topics list
        data5 = {
            'tile_input': f'{{"course_id":{subject_id},"layer":1,"page":1,"parent_id":{batch_id},"revert_api":"1#0#0#1","tile_id":"0","type":"content"}}',
            'csrf_name': token
        }
        Key = '%!$!%_$&!%F)&^!^'.encode('utf-8') 
        iv = '#*y*#2yJ*#$wJv*v'.encode('utf-8')   
        cipher = AES.new(Key, AES.MODE_CBC, iv)
        padded_data = pad(data5['tile_input'].encode(), AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        encoded_data = base64.b64encode(encrypted_data).decode()
        data5['tile_input'] = encoded_data

        res5 = requests.post(
            "https://online.utkarsh.com/web/Course/tiles_data", 
            headers=headers, 
            data=data5, 
            timeout=TIMEOUT
        ).json()["response"].replace('MDE2MTA4NjQxMDI3NDUxNQ==','==').replace(':', '==')
        
        decres5 = decrypt(res5)
        res5l = json.loads(decres5)
        resp5 = res5l.get("data", {})

        if not resp5:
            return []
        
        res5list = resp5.get("list", [])
        topic_ids = [str(id["id"]) for id in res5list]
        
        all_topic_urls = []
        total_topics = len(topic_ids)
        processed_topics = 0
        last_update_time = time.time()
        
        # Process topics with improved concurrency
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Process topics in smaller chunks to prevent overload
            chunk_size = 5
            for i in range(0, len(topic_ids), chunk_size):
                chunk = topic_ids[i:i + chunk_size]
                futures = []
                
                for t in chunk:
                    future = executor.submit(
                        process_topic, 
                        subject_id, 
                        t, 
                        batch_id, 
                        headers, 
                        token, 
                        Key, 
                        iv
                    )
                    futures.append(future)
                
                # Process chunk results
                for future in as_completed(futures):
                    try:
                        topic_urls = future.result()
                        if topic_urls:
                            all_topic_urls.extend(topic_urls)
                        
                        processed_topics += 1
                        current_time = time.time()
                        
                        # Update progress less frequently
                        if current_time - last_update_time >= UPDATE_INTERVAL:
                            elapsed = current_time - start_time
                            eta = (elapsed / processed_topics) * (total_topics - processed_topics) if processed_topics > 0 else 0
                            
                            progress_text = (
                                f"🔄 <b>Processing Large Batch</b>\n"
                                f"├─ Subject: {current_subject}/{total_subjects}\n"
                                f"├─ Name: <code>{topicName}</code>\n"
                                f"├─ Topics: {processed_topics}/{total_topics}\n"
                                f"├─ Links: {len(all_topic_urls)}\n"
                                f"├─ Time: {str(timedelta(seconds=int(elapsed)))}\n"
                                f"└─ ETA: {str(timedelta(seconds=int(eta)))}"
                            )
                            last_update_time = await update_progress_safely(progress_msg, progress_text, last_update_time)
                            
                    except Exception as e:
                        print(colored(f"  ⚠️ Error processing topic: {e}", "yellow"))
                        continue
                
                # Small delay between chunks
                await asyncio.sleep(1)
        
        # Clean up checkpoint after successful processing
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
            
        return all_topic_urls
        
    except Exception as e:
        print(colored(f"  ❌ Error processing subject {topicName}: {e}", "red"))
        return []

def process_topic(subject_id, topic_id, batch_id, headers, token, Key, iv):
    """Process a single topic (runs in thread)"""
    try:
        data5 = {
            'tile_input': f'{{"course_id":{subject_id},"parent_id":{batch_id},"layer":2,"page":1,"revert_api":"1#0#0#1","subject_id":{topic_id},"tile_id":0,"topic_id":{topic_id},"type":"content"}}',
            'csrf_name': token
        }
        
        cipher = AES.new(Key, AES.MODE_CBC, iv)
        padded_data = pad(data5['tile_input'].encode(), AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        encoded_data = base64.b64encode(encrypted_data).decode()
        data5['tile_input'] = encoded_data
        
        res6 = requests.post(
            "https://online.utkarsh.com/web/Course/tiles_data", 
            headers=headers, 
            data=data5, 
            timeout=TIMEOUT
        ).json()["response"].replace('MDE2MTA4NjQxMDI3NDUxNQ==','==').replace(':', '==')
        
        decres6 = decrypt(res6)
        res6l = json.loads(decres6)
        resp5 = res6l.get("data", {})
        
        if not resp5:
            return []
        
        res6list = resp5.get("list", [])
        topic_idss = [str(id["id"]) for id in res6list]
        
        topic_urls = []
        for tt in topic_idss:
            try:
                data6 = {
                    'layer_two_input_data': f'{{"course_id":{subject_id},"parent_id":{batch_id},"layer":3,"page":1,"revert_api":"1#0#0#1","subject_id":{topic_id},"tile_id":0,"topic_id":{tt},"type":"content"}}',
                    'content': 'content',
                    'csrf_name': token
                }
                encoded_data = base64.b64encode(data6['layer_two_input_data'].encode()).decode()
                data6['layer_two_input_data'] = encoded_data
                
                res6 = requests.post(
                    "https://online.utkarsh.com/web/Course/get_layer_two_data", 
                    headers=headers, 
                    data=data6, 
                    timeout=TIMEOUT
                ).json()["response"].replace('MDE2MTA4NjQxMDI3NDUxNQ==','==').replace(':', '==')
                
                decres6 = decrypt(res6)
                res6_json = json.loads(decres6)
                res6data = res6_json.get('data', {})
                
                if not res6data:
                    continue
                
                res6_list = res6data.get('list', [])
                for item in res6_list:
                    title = item.get("title", "").replace("||", "-").replace(":", "-")
                    bitrate_urls = item.get("bitrate_urls", [])
                    url = None
                    
                    for url_data in bitrate_urls:
                        if url_data.get("title") == "720p":
                            url = url_data.get("url")
                            break
                        elif url_data.get("name") == "720x1280.mp4":
                            url = url_data.get("link") + ".mp4"
                            url = url.replace("/enc/", "/plain/")
                        
                    if url is None:
                        url = item.get("file_url")
                    
                    if url and not url.endswith('.ws'):
                        if url.endswith(("_0_0", "_0")):
                            url = "https://apps-s3-jw-prod.utkarshapp.com/admin_v1/file_library/videos/enc_plain_mp4/{}/plain/720x1280.mp4".format(url.split("_")[0])
                        elif not url.startswith("https://") and not url.startswith("http://"):
                            url = f"https://youtu.be/{url}"
                        cc = f'{title}: {url}'
                        topic_urls.append(cc)
                        
            except Exception as e:
                print(colored(f"  ⚠️ Error processing subtopic {tt}: {e}", "yellow"))
                continue
                
        return topic_urls
        
    except Exception as e:
        print(colored(f"  ⚠️ Error processing topic {topic_id}: {e}", "yellow"))
        return []

async def process_batch_subjects(app, subject_ids, subject_list, batch_id, headers, token, progress_msg, bname):
    """Process subjects with improved stability for large batches"""
    all_urls = []
    total_subjects = len(subject_ids)
    batch_start_time = time.time()
    last_update_time = 0
    
    # Check for existing checkpoint
    start_index = 0
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                checkpoint = json.load(f)
                if checkpoint.get("batch_id") == batch_id:
                    start_index = checkpoint.get("current_subject", 0) - 1
                    print(colored(f"📝 Resuming from checkpoint: Subject {start_index + 1}", "cyan"))
        except:
            pass
    
    for idx, subject_id in enumerate(subject_ids[start_index:], start_index + 1):
        try:
            # Process subject
            subject_urls = await process_single_subject(
                app, 
                subject_id, 
                subject_list, 
                batch_id, 
                headers, 
                token, 
                progress_msg,
                idx,
                total_subjects
            )
            
            if subject_urls:
                all_urls.extend(subject_urls)
            
            # Update batch progress less frequently
            current_time = time.time()
            if current_time - last_update_time >= UPDATE_INTERVAL:
                elapsed = current_time - batch_start_time
                eta = (elapsed / idx) * (total_subjects - idx) if idx > 0 else 0
                
                progress_text = (
                    f"📦 <b>Large Batch Progress</b>\n"
                    f"├─ Completed: {idx}/{total_subjects} subjects\n"
                    f"├─ Total Links: {len(all_urls)}\n"
                    f"├─ Time: {str(timedelta(seconds=int(elapsed)))}\n"
                    f"└─ ETA: {str(timedelta(seconds=int(eta)))}"
                )
                last_update_time = await update_progress_safely(progress_msg, progress_text, last_update_time)
            
            # Small delay between subjects
            await asyncio.sleep(1)
            
        except Exception as e:
            print(colored(f"❌ Error processing subject: {e}", "red"))
            continue
            
    return all_urls

async def login(app, user_id, m, all_urls, start_time, bname, batch_id, progress_msg, app_name="Utkarsh", price=None, start_date=None, imageUrl=None):
    try:
        bname = await sanitize_bname(bname)
        file_path = f"{bname}.txt"
        
        await safe_edit_message(progress_msg, "💾 Creating file with extracted URLs...")
        
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(f"IMAGE: {TXT_LOGO_URL}\n\n")
            await f.writelines([url + '\n' for url in all_urls])
            
        # Analyze content types
        all_text = "\n".join(all_urls)
        video_count = len([url for url in all_urls if any(ext in url.lower() for ext in ['.mp4', '.m3u8', '.mpd', 'youtu.be', 'youtube.com'])])
        pdf_count = len([url for url in all_urls if '.pdf' in url.lower()])
        drm_count = len([url for url in all_urls if any(ext in url.lower() for ext in ['.mpd', '.m3u8', 'drm'])])
        image_count = len([url for url in all_urls if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif'])])
        doc_count = len([url for url in all_urls if any(ext in url.lower() for ext in ['.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx'])])
        other_count = len(all_urls) - (video_count + pdf_count + image_count + doc_count)
        
        # Get user info
        user = await app.get_users(user_id)
        contact_link = f"[{user.first_name}](tg://openmessage?user_id={user_id})"
        
        # Prepare statistics
        local_time = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        formatted_time = local_time.strftime("%d-%m-%Y %H:%M:%S")
        end_time = datetime.datetime.now()
        duration = end_time - start_time
        minutes, seconds = divmod(duration.total_seconds(), 60)
        
        # Prepare modern caption with emojis and formatting
        caption = (
            f"🎓 <b>COURSE EXTRACTED</b> 🎓\n\n"
            f"📱 <b>APP:</b> {app_name}\n"
            f"📚 <b>BATCH:</b> {bname} (ID: {batch_id})\n"
            f"⏱ <b>EXTRACTION TIME:</b> {int(minutes):02d}:{int(seconds):02d}\n"
            f"📅 <b>DATE:</b> {formatted_time} IST\n\n"
            f"📊 <b>CONTENT STATS</b>\n"
            f"├─ 📁 Total Links: {len(all_urls)}\n"
            f"├─ 🎬 Videos: {video_count}\n"
            f"├─ 📄 PDFs: {pdf_count}\n"
            f"├─ 🖼 Images: {image_count}\n"
            f"├─ 📑 Documents: {doc_count}\n"
            f"├─ 📦 Others: {other_count}\n"
            f"└─ 🔐 Protected: {drm_count}\n\n"
            f"🚀 <b>Extracted by</b>: @{(await app.get_me()).username}\n\n"
            f"<code>╾───• DREAM EXTRACTOR BOT 🚀 •───╼</code>"
        )
        
        # Send file with thumbnail
        await safe_edit_message(progress_msg, "📤 Uploading file with extracted links...")
        
        try:
            # Use cached thumbnail if available or download
            thumb_path = "Extractor/thumbs/txt-5.jpg" if os.path.exists("Extractor/thumbs/txt-5.jpg") else None
            if not thumb_path and THUMB_URL:
                thumb_path = f"thumb_{bname}.jpg"
                async with aiofiles.open(thumb_path, 'wb') as f:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(THUMB_URL) as response:
                            await f.write(await response.read())
            
            # Send document
            if thumb_path and os.path.exists(thumb_path):
                copy = await m.reply_document(
                    document=file_path,
                    caption=caption,
                    thumb=thumb_path
                )
                await app.send_document(txt_dump, file_path, caption=caption)
            else:
                copy = await m.reply_document(document=file_path, caption=caption)
                await app.send_document(txt_dump, file_path, caption=caption)
            
            await progress_msg.delete()
            print(colored("✅ File sent successfully!", "green"))
            
            # Print summary in terminal
            print(colored("\n📊 EXTRACTION SUMMARY:", "cyan"))
            print(colored(f"📚 Batch: {bname}", "white"))
            print(colored(f"📁 Total Links: {len(all_urls)}", "white"))
            print(colored(f"🎬 Videos: {video_count}", "white"))
            print(colored(f"📄 PDFs: {pdf_count}", "white"))
            print(colored(f"🖼 Images: {image_count}", "white"))
            print(colored(f"📑 Documents: {doc_count}", "white"))
            print(colored(f"📦 Others: {other_count}", "white"))
            print(colored(f"🔐 Protected: {drm_count}", "white"))
            print(colored(f"⏱️ Process took: {int(minutes):02d}:{int(seconds):02d}", "white"))
            
        except Exception as e:
            await safe_edit_message(progress_msg, f"❌ Error sending file: {str(e)}")
            print(colored(f"❌ Error sending file: {e}", "red"))
        finally:
            if thumb_path and os.path.exists(thumb_path):
                try:
                    os.remove(thumb_path)
                except:
                    pass
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            
    except Exception as e:
        print(colored(f"❌ Error in login function: {e}", "red"))
        await safe_edit_message(progress_msg, f"❌ Error: {str(e)}")

async def sanitize_bname(bname, max_length=50):
    """Clean batch name for safe file operations with advanced sanitization"""
    if not bname:
        return "Unknown_Batch"
        
    # Remove invalid filename characters
    bname = re.sub(r'[\\/:*?"<>|\t\n\r]+', '', bname).strip()
    
    # Replace spaces with underscores for better filenames
    bname = bname.replace(' ', '_')
    
    # Limit length
    if len(bname) > max_length:
        bname = bname[:max_length]
        
    # Ensure ASCII compatibility
    bname = ''.join(c for c in bname if ord(c) < 128)
    
    # If empty after sanitization, use default
    if not bname:
        bname = "Unknown_Batch"
        
    return bname