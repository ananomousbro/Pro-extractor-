import requests
import json
import random
import uuid
import time
import asyncio
import io
import aiohttp
from pyrogram import Client, filters
import os
from Extractor import app
import cloudscraper
import concurrent.futures
import re
from config import PREMIUM_LOGS, join, BOT_TEXT, THUMB_URL, TXT_LOGO_URL
from datetime import datetime
import pytz
from Extractor.core.utils import forward_to_log, send_to_log
import base64
from urllib.parse import urlparse, parse_qs

india_timezone = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(india_timezone)
time_new = current_time.strftime("%d-%m-%Y %I:%M %p")


apiurl = "https://api.classplusapp.com"
s = cloudscraper.create_scraper()


def parse_org_and_mobile(user_input: str):
    """
    Parse ORG code and 10-digit mobile number from various user formats:
    - PIKRT*7498987488
    - (PIKRT*7498987488)
    - pikrt * 7498987488
    - PIKRT*+917498987488
    - PIKRT*07498987488
    - 7498987488*PIKRT
    - PIKRT:7498987488
    - PIKRT 7498987488
    """
    raw = user_input.strip()
    # Strip any enclosing brackets, parentheses, quotes
    raw = re.sub(r"^[\(\[\{\"\']+|[\)\]\}\"\']+$", "", raw).strip()

    delimiters = ["*", ":", "/", " "]
    found_delim = None
    for d in delimiters:
        if d in raw:
            found_delim = d
            break

    if not found_delim:
        return None, None

    parts = raw.split(found_delim, 1)
    p1 = re.sub(r"[^a-zA-Z0-9_-]", "", parts[0]).strip()
    p2 = re.sub(r"\D", "", parts[1]).strip()

    # Normalize 10-digit Indian mobile
    if len(p2) == 12 and p2.startswith("91"):
        p2 = p2[2:]
    elif len(p2) == 11 and p2.startswith("0"):
        p2 = p2[1:]

    # Check if user sent MOBILE*ORG instead
    if p1.isdigit() and len(p1) >= 10:
        mob_candidate = p1
        if len(mob_candidate) == 12 and mob_candidate.startswith("91"):
            mob_candidate = mob_candidate[2:]
        elif len(mob_candidate) == 11 and mob_candidate.startswith("0"):
            mob_candidate = mob_candidate[1:]
        org_candidate = re.sub(r"[^a-zA-Z0-9_-]", "", parts[1]).strip()
        if len(mob_candidate) == 10 and org_candidate:
            return org_candidate.upper(), mob_candidate

    if p1 and len(p2) == 10:
        return p1.upper(), p2

    return None, None


def find_token(obj):
    """Recursively search for an auth token or JWT in any dict, list, or string."""
    if isinstance(obj, str):
        val = obj.strip()
        if val.startswith("eyJ") or (len(val) > 24 and " " not in val and not val.startswith("http")):
            return val
        return None
    elif isinstance(obj, dict):
        priority_keys = ["token", "accessToken", "access_token", "userToken", "jwt", "authToken", "x-access-token"]
        for key in priority_keys:
            if key in obj:
                val = obj[key]
                if isinstance(val, str) and (val.startswith("eyJ") or len(val) > 20):
                    return val.strip()
                elif isinstance(val, dict):
                    t = find_token(val)
                    if t:
                        return t
        for k, v in obj.items():
            if isinstance(v, str) and (v.startswith("eyJ") or (len(v) > 24 and " " not in v and not v.startswith("http"))):
                return v.strip()
            elif isinstance(v, (dict, list)):
                t = find_token(v)
                if t:
                    return t
    elif isinstance(obj, list):
        for item in obj:
            t = find_token(item)
            if t:
                return t
    return None


def fetch_user_courses(token: str):
    """Try multiple header configurations and endpoints to discover active courses/batches."""
    header_variants = [
        {
            'x-access-token': token,
            'user-agent': 'Mobile-Android',
            'app-version': '1.4.98.1',
            'api-version': '51',
            'device-id': str(uuid.uuid4()).replace('-', '')[:16]
        },
        {
            'x-access-token': token,
            'user-agent': 'Mobile-Android',
            'app-version': '1.4.65.3',
            'api-version': '29',
            'device-id': '39F093FF35F201D9'
        },
        {
            'x-access-token': token,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'accept': 'application/json, text/plain, */*',
            'region': 'IN'
        }
    ]

    courses_found = {}
    last_err = "No courses found"
    endpoints_to_try = [
        f"{apiurl}/v2/courses?tabCategoryId=1",
        f"{apiurl}/v2/courses",
        f"{apiurl}/v2/batches"
    ]

    for hdrs in header_variants:
        for ep in endpoints_to_try:
            try:
                resp = s.get(ep, headers=hdrs, timeout=12)
                if resp.status_code == 200:
                    r_data = resp.json().get("data", {})
                    c_list = r_data.get("courses") or r_data.get("batches") or []
                    if isinstance(c_list, list) and len(c_list) > 0:
                        for c in c_list:
                            c_id = c.get("id") or c.get("batchId")
                            c_name = c.get("name") or c.get("batchName")
                            if c_id and c_name:
                                courses_found[c_id] = c_name
                        if courses_found:
                            return courses_found, ""
                else:
                    try:
                        err_j = resp.json()
                        if err_j.get("message"):
                            last_err = err_j["message"]
                    except Exception:
                        pass
            except Exception:
                pass
    return courses_found, last_err


@app.on_message(filters.command(["cp"]))
async def classplus_txt(app, message):
    # Step 1: Ask for details
    details = await app.ask(message.chat.id, 
        "🔹 <b>CLASSPLUS EXTRACTOR 🚀</b> 🔹\n\n"
        "Send your details in any format:\n\n"
        "1️⃣ <b>ORG Code only</b> (e.g. <code>ABCD</code>)\n"
        "└─ <i>Extract courses directly without login</i>\n\n"
        "2️⃣ <b>ORG_CODE*Mobile</b> (e.g. <code>PIKRT*7498987488</code>)\n"
        "└─ <i>Login via OTP</i>\n\n"
        "3️⃣ <b>Access Token</b> (<code>eyJhbGci...</code>)\n"
        "└─ <i>Direct token login</i>\n\n"
        "Send your ORG code or details now (or /cancel to abort):"
    )
    if not details or not details.text:
        return
    await forward_to_log(details, "Classplus Extractor")
    user_input = details.text.strip()

    if user_input.lower() == "/cancel":
        await message.reply_text("❌ प्रक्रिया रद्द कर दी गई।")
        return

    # Check for ORG*Mobile format
    org_code, mobile = parse_org_and_mobile(user_input)

    if org_code and mobile:
        try:
            device_id = str(uuid.uuid4()).replace('-', '')
            headers = {
                "Accept": "application/json, text/plain, */*",
                "region": "IN",
                "accept-language": "en",
                "Content-Type": "application/json;charset=utf-8",
                "Api-Version": "51",
                "device-id": device_id,
                "User-Agent": "Mobile-Android"
            }
            # Clear any stale token header from previous logins
            s.headers.pop('x-access-token', None)

            status_msg = await message.reply_text(f"⏳ <b>Fetching details for ORG:</b> <code>{org_code}</code>...")

            # Step 2: Fetch Organization Details
            try:
                org_res = s.get(f"{apiurl}/v2/orgs/{org_code}", headers=headers, timeout=15)
                org_data = org_res.json()
            except Exception as e:
                await status_msg.edit_text(f"❌ <b>Connection Error:</b> {e}")
                return

            if org_res.status_code != 200 or not isinstance(org_data.get("data"), dict) or "orgId" not in org_data["data"]:
                msg = org_data.get("message", "Org not found") if isinstance(org_data, dict) else "Org not found"
                await status_msg.edit_text(
                    f"❌ <b>Invalid ORG Code:</b> <code>{org_code}</code> क्लासप्लस पर नहीं मिला!\n"
                    f"⚠️ <b>Server Message:</b> {msg}\n\n"
                    "कृपया ORG Code की स्पेलिंग जांचें और पुनः प्रयास करें।"
                )
                return

            org_id = org_data["data"]["orgId"]
            org_name = org_data["data"].get("orgName", org_code)

            # Step 3: Generate OTP
            otp_payload = {
                'countryExt': '91',
                'orgCode': org_code,
                'viaSms': '1',
                'mobile': mobile,
                'orgId': org_id,
                'otpCount': 0
            }

            try:
                otp_response = s.post(f"{apiurl}/v2/otp/generate", json=otp_payload, headers=headers, timeout=15)
                otp_data = otp_response.json()
            except Exception as e:
                await status_msg.edit_text(f"❌ <b>Error sending OTP request:</b> {e}")
                return

            session_id = None
            if isinstance(otp_data, dict):
                session_id = otp_data.get('data', {}).get('sessionId') if isinstance(otp_data.get('data'), dict) else None

            if not session_id:
                # Fallback: try with org_name if different
                if org_name and org_name != org_code:
                    otp_payload['orgCode'] = org_name
                    try:
                        otp_response = s.post(f"{apiurl}/v2/otp/generate", json=otp_payload, headers=headers, timeout=15)
                        otp_data = otp_response.json()
                        if isinstance(otp_data, dict):
                            session_id = otp_data.get('data', {}).get('sessionId') if isinstance(otp_data.get('data'), dict) else None
                    except Exception:
                        pass

            if not session_id:
                raw_reason = otp_data.get("message", "Could not send OTP") if isinstance(otp_data, dict) else str(otp_response.text)
                err_reason = raw_reason
                lower_reason = raw_reason.lower()
                if any(k in lower_reason for k in ["limit", "wait", "many", "cooldown", "exceeded", "seconds", "minute", "time"]):
                    err_reason = f"{raw_reason}\n\n⏳ <b>क्लासप्लस ने इस नंबर पर अस्थायी रोक (Rate Limit / Cooldown) लगाई है।</b>\nकृपया 1 से 2 मिनट रुककर दोबारा प्रयास करें।"

                await status_msg.edit_text(
                    f"❌ <b>OTP भेजने में समस्या आई!</b>\n\n"
                    f"🏢 <b>Institute:</b> {org_name} (<code>{org_code}</code>)\n"
                    f"📱 <b>Mobile:</b> <code>+91 {mobile}</code>\n"
                    f"⚠️ <b>कारण:</b> {err_reason}\n\n"
                    "कृपया 1-2 मिनट बाद पुनः प्रयास करें।"
                )
                return

            try:
                await status_msg.delete()
            except Exception:
                pass

            # Step 4: Ask for OTP
            user_otp = await app.ask(
                message.chat.id, 
                "📱 <b>OTP Verification</b>\n\n"
                f"✅ OTP has been sent via SMS to <b>+91 {mobile}</b>\n"
                f"🏢 <b>Institute:</b> {org_name} (<code>{org_code}</code>)\n\n"
                "Please enter the OTP to continue (or send /cancel to abort):", 
                timeout=300
            )

            if not user_otp or not user_otp.text:
                await message.reply_text("⏱️ <b>Timeout:</b> आपने समय पर OTP दर्ज नहीं किया।")
                return

            raw_otp = user_otp.text.strip()
            if raw_otp.lower() == "/cancel":
                await message.reply_text("❌ प्रक्रिया रद्द कर दी गई।")
                return

            clean_otp = re.sub(r"\D", "", raw_otp)
            if not clean_otp:
                await message.reply_text("❌ <b>अमान्य OTP!</b> कृपया केवल अंक दर्ज करें।")
                return

            # Step 5: Verify OTP
            fingerprint_id = str(uuid.uuid4()).replace('-', '')
            verify_payload = {
                "otp": clean_otp,
                "countryExt": "91",
                "sessionId": session_id,
                "orgId": org_id,
                "fingerprintId": fingerprint_id,
                "mobile": mobile
            }

            verify_response = s.post(f"{apiurl}/v2/users/verify", json=verify_payload, headers=headers, timeout=15)
            verify_data = {}
            try:
                verify_data = verify_response.json()
            except Exception:
                pass

            # First: Extract token directly from verify response or response headers
            token = find_token(verify_data) or verify_response.headers.get('x-access-token')

            # Second: If token is not present and verify succeeded or registration is needed (e.g. 200, 201, 409)
            if not token and (verify_response.status_code in [200, 201, 409] or verify_data.get("message") == "Verify successful"):
                email = str(uuid.uuid4()).replace('-', '') + "@gmail.com"
                reg_payload = {
                    "contact": {
                        "email": email,
                        "countryExt": "91",
                        "mobile": mobile
                    },
                    "fingerprintId": fingerprint_id,
                    "name": "name",
                    "orgId": org_id,
                    "orgName": org_name,
                    "otp": clean_otp,
                    "sessionId": session_id,
                    "type": 1,
                    "viaEmail": 0,
                    "viaSms": 1
                }
                try:
                    reg_response = s.post(f"{apiurl}/v2/users/register", json=reg_payload, headers=headers, timeout=15)
                    reg_data = reg_response.json()
                    token = find_token(reg_data) or reg_response.headers.get('x-access-token')
                except Exception:
                    pass

                if not token and org_name != org_code:
                    reg_payload["orgName"] = org_code
                    try:
                        reg_response = s.post(f"{apiurl}/v2/users/register", json=reg_payload, headers=headers, timeout=15)
                        reg_data = reg_response.json()
                        token = find_token(reg_data) or reg_response.headers.get('x-access-token')
                    except Exception:
                        pass

            if token:
                s.headers['x-access-token'] = token
                await message.reply_text(
                    "✅ <b>Login Successful!</b>\n\n"
                    "🔑 <b>Your Access Token:</b>\n"
                    f"<code>{token}</code>"
                )
                try:
                    await app.send_message(
                        PREMIUM_LOGS, 
                        "✅ <b>New Classplus Login Alert</b>\n\n"
                        f"🏢 <b>Org:</b> {org_name} (<code>{org_code}</code>)\n"
                        f"📱 <b>Mobile:</b> <code>{mobile}</code>\n"
                        f"🔑 <b>Token:</b>\n<code>{token}</code>"
                    )
                except Exception:
                    pass

                # Fetch courses
                courses_found, _ = fetch_user_courses(token)
                if courses_found:
                    s.session_data = {"token": token, "courses": courses_found}
                    await fetch_batches(app, message, org_name)
                else:
                    await message.reply_text("⚠️ <b>लॉगिन सफल रहा</b>, लेकिन इस अकाउंट में कोई एक्टिव कोर्स/बैच नहीं मिला।")
            else:
                raw_err = verify_data.get("message", "Invalid OTP or login failed") if isinstance(verify_data, dict) else "Wrong OTP"
                if raw_err == "Verify successful":
                    err_msg = "OTP सत्यापित हुआ लेकिन क्लासप्लस सर्वर से ऑथराइजेशन टोकन प्राप्त नहीं हो सका। कृपया पुनः प्रयास करें।"
                else:
                    err_msg = raw_err
                await message.reply_text(f"❌ <b>लॉगिन असफल:</b> {err_msg}")

        except Exception as e:
            await message.reply_text(f"❌ <b>Error:</b> {str(e)}")

    elif "*" in user_input:
        # User attempted ORG*MOBILE but entered invalid mobile/format
        await message.reply_text(
            "❌ <b>अमान्य फॉर्मेट!</b>\n\n"
            "कृपया 10-अंकों का मोबाइल नंबर और ORG कोड सही तरीके से भेजें:\n"
            "👉 <code>ORG_CODE*MOBILE</code>\n"
            "उदाहरण: <code>PIKRT*7498987488</code>"
        )
        return

    elif len(user_input) > 20:
        # Check if the token is actually an AppX / ClassX token
        is_appx_token = False
        appx_info = None
        try:
            parts = user_input.split(".")
            if len(parts) >= 2:
                padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
                jwt_data = json.loads(base64.b64decode(padded).decode('utf-8', errors='ignore'))
                
                # Check for AppX signature
                session_raw = jwt_data.get("session")
                tenant_name = jwt_data.get("tenantName")
                if session_raw and isinstance(session_raw, str) and "." in session_raw:
                    s_parts = session_raw.split(".")
                    s_padded = s_parts[1] + "=" * ((4 - len(s_parts[1]) % 4) % 4)
                    s_data = json.loads(base64.b64decode(s_padded).decode('utf-8', errors='ignore'))
                    tenant_name = s_data.get("tenantName") or tenant_name
                
                if tenant_name or jwt_data.get("tenantType") or "iv_ver" in jwt_data:
                    is_appx_token = True
                    appx_info = tenant_name
        except Exception:
            pass

        if is_appx_token:
            clean_name = (appx_info or "").replace("_db", "").replace("live", " Live").title() if appx_info else "AppX"
            suggested_api = "websankulliveapi.classx.co.in" if "websankul" in str(appx_info).lower() else "your_coaching_api.classx.co.in"
            await message.reply_text(
                "⚠️ <b>यह Classplus का टोकन नहीं है!</b>\n\n"
                f"📌 यह टोकन <b>AppX / ClassX ({clean_name})</b> का है।\n\n"
                "👉 <b>लॉगिन करने के लिए सही तरीका:</b>\n"
                "1️⃣ बोट में <code>/appx</code> कमांड भेजें।\n"
                f"2️⃣ API URL में डालें: <code>{suggested_api}</code>\n"
                "3️⃣ फिर यह टोकन पेस्ट करें।"
            )
            return

        a = f"CLASSPLUS LOGIN ATTEMPT FOR\n\n<blockquote>`{user_input}`</blockquote>"
        await app.send_message(PREMIUM_LOGS, a)

        courses_found, last_error_msg = fetch_user_courses(user_input)

        if courses_found:
            s.session_data = {
                "token": user_input,
                "courses": courses_found
            }

            org_name = "Classplus"
            await fetch_batches(app, message, org_name)
        else:
            await message.reply(
                f"❌ <b>Login Failed:</b> {last_error_msg}\n\n"
                "⚠️ कृपया सुनिश्चित करें कि:\n"
                "• टोकन एक्सपायर न हुआ हो\n"
                "• टोकन Classplus ऐप या web.classplusapp.com का ही हो"
            )
    else:
        # User entered ORG Code (e.g. ABCD)
        org_code = user_input.strip()
        uid = details.from_user.id if details.from_user else message.chat.id
        try:
            from Extractor.modules.freecp import process_cpwp
            await process_cpwp(app, details, uid, initial_org_code=org_code)
        except Exception as e:
            await message.reply(f"Error processing ORG code: {e}")



async def fetch_batches(app, message, org_name):
    session_data = s.session_data
    
    if "courses" in session_data:
        courses = session_data["courses"]
        
        
      
        text = "📚 <b>Available Batches</b>\n\n"
        course_list = []
        for idx, (course_id, course_name) in enumerate(courses.items(), start=1):
            text += f"{idx}. <code>{course_name}</code>\n"
            course_list.append((idx, course_id, course_name))
        
        await app.send_message(PREMIUM_LOGS, f"<blockquote>{text}</blockquote>")
        selected_index = await app.ask(
            message.chat.id, 
            f"{text}\n"
            "Send the index number of the batch to download.", 
            timeout=180
        )
        
        if selected_index.text.isdigit():
            selected_idx = int(selected_index.text.strip())
            
            if 1 <= selected_idx <= len(course_list):
                selected_course_id = course_list[selected_idx - 1][1]
                selected_course_name = course_list[selected_idx - 1][2]

                prompt_text = (
                    f"✅ **Batch selected:** {selected_course_name}\n\n"
                    "**Choose extraction type:**\n\n"
                    "1️⃣ 1 — 📦 **Full Batch**\n"
                    "2️⃣ 2 — 📅 **Today's Class**"
                )
                opt_msg = await app.ask(message.chat.id, text=prompt_text, timeout=120)
                ext_type = opt_msg.text.strip() if opt_msg and opt_msg.text else "1"
                
                await app.send_message(
                    message.chat.id,
                    "🔄 <b>Processing Course</b>\n"
                    f"└─ Current: <code>{selected_course_name}</code>"
                )
                await extract_batch(app, message, org_name, selected_course_id, ext_type)
            else:
                await app.send_message(
                    message.chat.id,
                    "❌ <b>Invalid Input!</b>\n\n"
                    "Please send a valid index number from the list."
                )
        else:
            await app.send_message(
                message.chat.id,
                "❌ <b>Invalid Input!</b>\n\n"
                "Please send a valid index number."
            )
              
    else:
        await app.send_message(
            message.chat.id,
            "❌ <b>No Batches Found</b>\n\n"
            "Please check your credentials and try again."
        )


async def extract_batch(app, message, org_name, batch_id, ext_type="1"):
    session_data = s.session_data
    
    if "token" in session_data:
        batch_name = session_data["courses"][batch_id]
        if ext_type == "2":
            batch_name = f"{batch_name} - Today's Class"

        headers = {
            'x-access-token': session_data["token"],
            'user-agent': 'Mobile-Android',
            'app-version': '1.4.65.3',
            'api-version': '29',
            'device-id': '39F093FF35F201D9'
        }

        def is_today_item(item_obj):
            today_ist = datetime.now(pytz.timezone('Asia/Kolkata')).date()
            date_fields = ["liveDate", "created_at", "createdAt", "addedDate", "scheduleDate", "publishedDate", "date", "startTime"]
            for fld in date_fields:
                val = item_obj.get(fld)
                if not val:
                    continue
                val_str = str(val)
                if today_ist.strftime('%Y-%m-%d') in val_str or today_ist.strftime('%d-%m-%Y') in val_str or today_ist.strftime('%d/%m/%Y') in val_str:
                    return True
                try:
                    num = float(val)
                    if num > 1e11:
                        num = num / 1000.0
                    dt = datetime.fromtimestamp(num, tz=pytz.timezone('Asia/Kolkata')).date()
                    if dt == today_ist:
                        return True
                except:
                    pass
            return False

        def clean_direct_url(url):
            return url.strip() if url else ""

        def resolve_video_m3u8(thumb_url):
            if not thumb_url:
                return ""
            url = thumb_url.strip()
            if "thumbnail.png" in url:
                url = url.replace("thumbnail.png", "master.m3u8")
            elif url.endswith((".jpg", ".jpeg", ".png")):
                url = url.rsplit("/", 1)[0] + "/master.m3u8"
            
            if "akamai-cdn.classplusapp.com/media/" in url and "/azure/" not in url:
                url = url.replace("akamai-cdn.classplusapp.com/media/", "akamai-cdn.classplusapp.com/azure/media/")
            elif "media-cdn.classplusapp.com/media/" in url and "/azure/" not in url:
                url = url.replace("media-cdn.classplusapp.com/media/", "media-cdn.classplusapp.com/azure/media/")
            return url

        async def fetch_live_videos(course_id):
            """Fetch live videos from the API with clean direct URLs."""
            outputs = []
            async with aiohttp.ClientSession() as session:
                try:
                    url = f"{apiurl}/v2/course/live/list/videos?type=2&entityId={course_id}&limit=9999&offset=0"
                    async with session.get(url, headers=headers) as response:
                        j = await response.json()
                        if "data" in j and "list" in j["data"]:
                            for video in j["data"]["list"]:
                                if ext_type == "2" and not is_today_item(video):
                                    continue
                                name = video.get("name", "Unknown Video")
                                video_url = video.get("url", "")
                                if not video_url or video_url.endswith(("thumbnail.png", ".png", ".jpg", ".jpeg")):
                                    video_url = resolve_video_m3u8(video.get("thumbnailUrl") or video_url)
                        
                                if video_url:
                                    clean_url = clean_direct_url(video_url)
                                    outputs.append(f"{name}: {clean_url}\n")
                except Exception as e:
                    print(f"Error fetching live videos: {e}")

            return outputs


        async def process_course_contents(course_id, folder_id=0, folder_path=""):
            """Recursively fetch and process course content with 100% clean direct URLs."""
            result = []
            url = f'{apiurl}/v2/course/content/get?courseId={course_id}&folderId={folder_id}'

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    course_data = await resp.json()
                    course_data = course_data.get("data", {}).get("courseContent", [])

            tasks = []
            for item in course_data:
                content_type = str(item.get("contentType"))
                sub_id = item.get("id")
                sub_name = item.get("name", "Untitled")

                if content_type == "2":  # Video
                    if ext_type == "2" and not is_today_item(item):
                        continue
                    video_url = item.get("url", "")
                    if not video_url or video_url.endswith(("thumbnail.png", ".png", ".jpg", ".jpeg")):
                        video_url = resolve_video_m3u8(item.get("thumbnailUrl") or video_url)
                    if video_url:
                        clean_url = clean_direct_url(video_url)
                        result.append(f"{folder_path}{sub_name}: {clean_url}\n")

                elif content_type == "3":  # Document / PDF
                    if ext_type == "2" and not is_today_item(item):
                        continue
                    pdf_url = item.get("url") or item.get("attachmentUrl") or item.get("documentUrl")
                    if pdf_url:
                        clean_url = clean_direct_url(pdf_url)
                        result.append(f"{folder_path}{sub_name}: {clean_url}\n")

                elif content_type == "1":  # Folder
                    new_folder_path = f"{folder_path}{sub_name} - "
                    tasks.append(process_course_contents(course_id, sub_id, new_folder_path))

            sub_contents = await asyncio.gather(*tasks)
            for sub_content in sub_contents:
                result.extend(sub_content)

            return result

        
        async def write_to_file(extracted_data):
            """Write data to a text file asynchronously."""
            invalid_chars = '\t:/+#|@*.'
            clean_name = ''.join(char for char in batch_name if char not in invalid_chars)
            clean_name = clean_name.replace('_', ' ')
            file_path = f"{clean_name}.txt"
            
            with open(file_path, "w", encoding='utf-8') as file:
                file.write(f"IMAGE: {TXT_LOGO_URL}\n\n" + ''.join(extracted_data))
            return file_path

        extracted_data, live_videos = await asyncio.gather(
            process_course_contents(batch_id),
            fetch_live_videos(batch_id)
        )

        extracted_data.extend(live_videos)

        if not extracted_data:
            if ext_type == "2":
                await app.send_message(
                    message.chat.id,
                    "❌ **आज इस बैच में कोई भी क्लास नहीं हुई है या आज का कोई लिंक उपलब्ध नहीं है।**"
                )
            else:
                await app.send_message(
                    message.chat.id,
                    "❌ **इस बैच में कोई सामग्री नहीं मिली।**"
                )
            return

        file_path = await write_to_file(extracted_data)

        # Count different types of content
        video_count = sum(1 for line in extracted_data if "Video" in line or ".mp4" in line)
        pdf_count = sum(1 for line in extracted_data if ".pdf" in line)
        total_links = len(extracted_data)
        other_count = total_links - (video_count + pdf_count)
        
        caption = (
            f"🎓 <b>COURSE EXTRACTED</b> 🎓\n\n"
            f"📱 <b>APP:</b> {org_name}\n"
            f"📚 <b>BATCH:</b> {batch_name}\n"
            f"📅 <b>DATE:</b> {time_new} IST\n\n"
            f"📊 <b>CONTENT STATS</b>\n"
            f"├─ 📁 Total Links: {total_links}\n"
            f"├─ 🎬 Videos: {video_count}\n"
            f"├─ 📄 PDFs: {pdf_count}\n"
            f"└─ 📦 Others: {other_count}\n\n"
            f"🚀 <b>Extracted by</b>: @{(await app.get_me()).username}\n\n"
            f"<code>╾───• {BOT_TEXT} •───╼</code>"
        )

        thumb_file = "Extractor/thumbs/txt-5.jpg" if os.path.exists("Extractor/thumbs/txt-5.jpg") else None
        try:
            await app.send_document(message.chat.id, file_path, caption=caption)
            await send_to_log(file_path, caption=caption, thumb=thumb_file)
        except Exception as e:
            print(f"Error sending classplus document: {e}")
        finally:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            

    
