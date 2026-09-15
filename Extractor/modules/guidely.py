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

GUIDELY_API_KEY = "qw42yunk"

@app.on_message(filters.command(["guidely"]))
async def guidely_login(client, message):
    try:
        start_time = datetime.now()
        
        editable = await message.reply_text(
            "🔹 <b>GUIDELY EXTRACTOR PRO</b> 🔹\n\n"
            "कृपया लॉगिन विवरण भेजें:\n"
            "1️⃣ <b>Mobile Number</b> (OTP के लिए)\n"
            "2️⃣ <b>Session / Token</b> सीधे पेस्ट करें\n\n"
            "<i>उदाहरण:</i>\n"
            "- Mobile: <code>9982121881</code>\n"
            "- Direct slug/batch link: <code>saviour-quant-batch-2025</code>"
        )

        input1 = await app.ask(message.chat.id, "अपना मोबाइल नंबर या बैच स्लग (Slug) भेजें:")
        raw_text = input1.text.strip()
        await forward_to_log(input1, "Guidely Extractor")
        await input1.delete()

        # Check if user sent mobile number
        if raw_text.isdigit() and len(raw_text) == 10:
            mobile_num = raw_text
            await editable.edit_text(f"⏳ मोबाइल नंबर <code>{mobile_num}</code> पर OTP भेजा जा रहा है...")

            login_url = f"https://webapi.guidely.in/mobile-login?apikey={GUIDELY_API_KEY}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Origin": "https://guidely.in",
                "Referer": "https://guidely.in/"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(login_url, json={"mobile": mobile_num}, headers=headers) as resp:
                    resp_data = await resp.json(content_type=None)
                    logger.info(f"Guidely mobile login response: {resp_data}")

            otp_prompt = await app.ask(message.chat.id, f"📲 आपके मोबाइल <code>{mobile_num}</code> पर आया हुआ OTP भेजें:")
            otp_val = otp_prompt.text.strip()
            await otp_prompt.delete()

            await editable.edit_text("⏳ OTP सत्यापित (Verify) किया जा रहा है...")
            verify_url = f"https://webapi.guidely.in/verify-mobile-login?apikey={GUIDELY_API_KEY}"
            async with aiohttp.ClientSession() as session:
                async with session.post(verify_url, json={"otp": otp_val, "mobile": int(mobile_num)}, headers=headers) as resp:
                    verify_data = await resp.json(content_type=None)
                    logger.info(f"Guidely OTP verify response: {verify_data}")
                    if not verify_data.get("status"):
                        await editable.edit_text(f"❌ <b>लॉगिन विफल!</b>\n\n{verify_data.get('message', 'अमान्य OTP')}")
                        return

            await editable.edit_text("✅ <b>लॉगिन सफल!</b>")
            batch_slug_prompt = await app.ask(message.chat.id, "अब Guidely बैच का नाम या Slug भेजें (जैसे: <code>saviour-quant-batch-2025</code>):")
            slug = batch_slug_prompt.text.strip()
            await batch_slug_prompt.delete()
        else:
            # User gave direct batch slug or URL
            slug = raw_text.split("/")[-1].replace(".html", "").strip()

        await editable.edit_text(f"⏳ बैच डेटा लोड हो रहा है: <code>{slug}</code>...")

        # Fetch video categories and product details
        cat_url = f"https://webapi.guidely.in/video-product-categories/{slug}?apikey={GUIDELY_API_KEY}"
        prod_url = f"https://webapi.guidely.in/video-product/{slug}?apikey={GUIDELY_API_KEY}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Origin": "https://guidely.in",
            "Referer": f"https://guidely.in/{slug}"
        }

        extracted_links = []
        async with aiohttp.ClientSession() as session:
            async with session.get(prod_url, headers=headers) as resp:
                if resp.status == 200:
                    try:
                        p_data = await resp.json(content_type=None)
                        if isinstance(p_data, dict) and "data" in p_data:
                            info = p_data["data"]
                            title = info.get("title", slug)
                            # Extract any attachment or video
                            if "demo_video" in info and info["demo_video"]:
                                extracted_links.append(f"Demo Video:{info['demo_video']}")
                    except Exception as e:
                        logger.error(f"Error parsing prod details: {e}")

            async with session.get(cat_url, headers=headers) as resp:
                if resp.status == 200:
                    try:
                        c_data = await resp.json(content_type=None)
                        # c_data can be dict or list
                        items = []
                        if isinstance(c_data, list):
                            items = c_data
                        elif isinstance(c_data, dict):
                            items = c_data.get("data") or c_data.get("categories") or [c_data]

                        for item in items:
                            if isinstance(item, dict):
                                c_name = item.get("name") or item.get("category_name") or item.get("title") or "Chapter"
                                # Look for nested videos or links
                                vids = item.get("videos") or item.get("classes") or []
                                for v in vids:
                                    v_title = v.get("title") or v.get("name") or "Video"
                                    v_url = v.get("video_url") or v.get("url") or v.get("m3u8") or v.get("pdf_url") or ""
                                    if v_url:
                                        extracted_links.append(f"{c_name} - {v_title}:{v_url}")
                    except Exception as e:
                        logger.error(f"Error parsing categories: {e}")

        if not extracted_links:
            # Add guidance or fallback message
            await editable.edit_text(
                f"ℹ️ <b>Guidely बैच: {slug}</b>\n\n"
                "इस बैच के लिए सीधे लिंक्स प्राप्त नहीं हुए। यदि यह DRM/Enrolled बैच है, तो कृपया लॉगिन टोकन या DRM सत्र का उपयोग करें।"
            )
            return

        file_name = f"Guidely_{slug}_{int(start_time.timestamp())}.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(f"IMAGE: {TXT_LOGO_URL}\n\n" + "\n".join(extracted_links))

        caption = (
            f"🎓 <b>COURSE EXTRACTED</b> 🎓\n\n"
            f"📱 <b>APP:</b> Guidely\n"
            f"📚 <b>BATCH:</b> {slug}\n"
            f"📊 <b>TOTAL LINKS:</b> {len(extracted_links)}\n"
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

        await editable.edit_text("✅ <b>Guidely एक्सट्रैक्शन सफलतापूर्वक पूरा हुआ!</b>")

    except Exception as e:
        logger.error(f"Error in guidely_login: {e}")
        await message.reply_text(f"❌ <b>Error:</b> <code>{str(e)}</code>")
