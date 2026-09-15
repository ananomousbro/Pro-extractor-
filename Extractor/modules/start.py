import re
import json
import random
import asyncio
import os
import requests
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from pyrogram import filters, Client
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ParseMode
from Extractor import app
from config import OWNER_ID, CHANNEL_ID, ADMIN_BOT_USERNAME, TXT_LOGO_URL, THUMB_URL, ADMINS
from Extractor.core import script
from Extractor.core.func import subscribe, chk_user
import datetime
import pytz
# from Extractor.modules.cdsfree import handle_cds_journey, handle_cds_callback, handle_batch_message
# from Extractor.modules.appex_v1 import api_v1
# from Extractor.modules.appex_v2 import appex_v2_txt
# from Extractor.modules.appex_v3 import appex_v5_txt
from Extractor.modules.appex_v4 import appex_v4_txt, appex_v5_txt
from Extractor.modules.classplus import classplus_txt
from Extractor.modules.pw import pw_login
from Extractor.modules.exampur import exampur_txt
from Extractor.modules.careerwill import career_will
from Extractor.modules.utk import handle_utk_logic
from Extractor.modules.ak import ak_start
from Extractor.modules.mypathshala import my_pathshala_login
from Extractor.modules.khan import khan_login
from Extractor.modules.kdlive import kdlive
from Extractor.modules.iq import handle_iq_logic
from Extractor.modules.getappxotp import send_otpp
from Extractor.modules.findapi import findapis_extract
from Extractor.modules.rg_vikramjeet import rgvikramjeet
from Extractor.modules.adda import adda_command_handler
from Extractor.modules.vision import scrape_vision_ias
from Extractor.modules.guidely import guidely_login
from Extractor.modules.oliveboard import oliveboard_login
from Extractor.modules.testbook import testbook_handler
from Extractor.core.utils import forward_to_log
from Extractor.modules.enc import *

from Extractor.modules.freecp import *
from Extractor.modules.freeappx import *
from Extractor.modules.freepw import *
# from Extractor.modules.cds import handle_cds_callback

from Extractor.core.mongo import plans_db
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import config
import logging
from Extractor.html_converter.bot import handle_txt2html, show_txt2html_help
from bs4 import BeautifulSoup
import base64

def is_admin(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in ADMINS

thumb_path = "Extractor/thumbs/txt-5.jpg"
THREADPOOL = ThreadPoolExecutor(max_workers=2000)
TIMEOUT = 300  # 5 minutes timeout

async def check_user_is_premium(user_id: int) -> bool:
    if is_admin(user_id):
        return True
    try:
        data = await plans_db.check_premium(user_id)
        if data and data.get("expire_date"):
            expiry = data["expire_date"]
            if hasattr(expiry, "tzinfo") and expiry.tzinfo is not None:
                now = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
                return expiry.astimezone(pytz.timezone("Asia/Kolkata")) > now
            else:
                return expiry > datetime.datetime.now()
    except Exception as e:
        print(f"Error checking premium: {e}")
    return False

# Dream Extractor Main Menu
buttons = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("👑 MASTER APPX 👑", callback_data="master_appx_menu")
    ],
    [
        InlineKeyboardButton("🎓 CLASSPLUS 🎓", callback_data="classplus_"),
        InlineKeyboardButton("📖 STUDY IQ 📖", callback_data="iq_")
    ],
    [
        InlineKeyboardButton("📚 ADDA 247 📚", callback_data="adda_"),
        InlineKeyboardButton("📝 PATHSHALA 📝", callback_data="my_pathshala_")
    ],
    [
        InlineKeyboardButton("⚡ PHYSICS WALLAH ⚡", callback_data="pw_")
    ],
    [
        InlineKeyboardButton("📱 KHAN GS 📱", callback_data="khan_"),
        InlineKeyboardButton("🏫 KD CAMPUS 🏫", callback_data="kdlive_")
    ],
    [
        InlineKeyboardButton("🏆 UTKARSH 🏆", callback_data="utkarsh_")
    ],
    [
        InlineKeyboardButton("🌟 EXAMPUR 🌟", callback_data="exampur_txt"),
        InlineKeyboardButton("👑 CAREERWILL 👑", callback_data="ugcw_")
    ],
    [
        InlineKeyboardButton("🎯 APNI KAKSHA 🎯", callback_data="ak_"),
        InlineKeyboardButton("🔭 VISION IAS 🔭", callback_data="vision_ias_")
    ],
    [
        InlineKeyboardButton("🛡 RG VIKRAMJEET 🛡", callback_data="rgvikramjeet_"),
        InlineKeyboardButton("🔒 NO LOGIN APPS 🔒", callback_data="custom_")
    ],
    [
        InlineKeyboardButton("📖 GUIDELY 📖", callback_data="guidely_"),
        InlineKeyboardButton("🎯 OLIVEBOARD 🎯", callback_data="oliveboard_")
    ],
    [
        InlineKeyboardButton("📚 TESTBOOK 📚", callback_data="testbook_"),
        InlineKeyboardButton("👑 STUDY IQ 👑", callback_data="iq_")
    ],
    [
        InlineKeyboardButton("📞 CONTACT ↗", url=f"https://t.me/{ADMIN_BOT_USERNAME}"),
        InlineKeyboardButton("🔍 CHANNEL ↗", url="https://t.me/nikbotchannel")
    ],
    [
        InlineKeyboardButton("👑 ᴀᴅᴍɪɴ ʜᴇʟᴘ (एडमिन गाइड) 👑", callback_data="admin_help_btn")
    ]
])

# Master Appx Menu
master_appx_buttons = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("📋 APPX LIST 📋", callback_data="appxlist"),
        InlineKeyboardButton("🔐 APPX OTP 🔐", callback_data="appx_otp")
    ],
    [
        InlineKeyboardButton("🔍 APPX API 🔍", callback_data="findapi_"),
        InlineKeyboardButton("📲 MANUAL API ENTRY 📲", callback_data="manual_api_entry")
    ],
    [
        InlineKeyboardButton("📝 TEXT ⟷ HTML 📝", callback_data="converter_")
    ],
    [
        InlineKeyboardButton("⬅️ BACK", callback_data="home_")
    ]
])

modes_button = [[
                  InlineKeyboardButton("🔏 Wɪᴛʜᴏᴜᴛ Lᴏɢɪɴ", callback_data="custom_")
                ],[
                  InlineKeyboardButton("🔑 Lᴏɢɪɴ", callback_data="manual_"),
                ],
                [
                  InlineKeyboardButton("𝐁 𝐀 𝐂 𝐊", callback_data="home_")
                ]]


custom_button = [[
                  InlineKeyboardButton("⚡ Pᴡ ⚡", callback_data="pwwp"),
                  InlineKeyboardButton("🔮 Aᴘᴘx 🔮", callback_data="appxwp"),
                ],[
                  InlineKeyboardButton("🎯 CʟᴀssPʟᴜs 🎯", callback_data="cpwp")
                  # InlineKeyboardButton("🎓 CDS Jᴏᴜʀɴᴇʏ 🎓", callback_data="cds_journey_free")
                ],[
                  InlineKeyboardButton("⬅️ 𝐁 𝐀 𝐂 𝐊", callback_data="home_")
                ]]

button1 = [              
                [
                    InlineKeyboardButton("👑 Aᴘɴɪ Kᴀᴋsʜᴀ", callback_data="ak_"),
                    InlineKeyboardButton("👑 Aᴅᴅᴀ 𝟸𝟺𝟽", callback_data="adda_")
                ],
                [
                    InlineKeyboardButton("👑 CʟᴀssPʟᴜs", callback_data="classplus_"),
                    InlineKeyboardButton("👑 Kʜᴀɴ Gs", callback_data="khan_")
                ],
                [
                    InlineKeyboardButton("👑 Pʜʏsɪᴄs Wᴀʟʟᴀʜ", callback_data="pw_"),
                    InlineKeyboardButton("👑 Sᴛᴜᴅʏ IQ", callback_data="iq_")
                ],
                [
                    InlineKeyboardButton("👑 Kᴅ Cᴀᴍᴘᴜs", callback_data="kdlive_"),
                    InlineKeyboardButton("👑 Uᴛᴋᴀʀsʜ", callback_data="utkarsh_")
                    # InlineKeyboardButton("👑 CDS Jᴏᴜʀɴᴇʏ", callback_data="cds_journey")
                ],
                [
                    InlineKeyboardButton("👑 Mʏ Pᴀᴛʜsʜᴀʟᴀ", callback_data="my_pathshala_"),
                    InlineKeyboardButton("👑 ExᴀᴍPᴜʀ", callback_data="exampur_txt")
                ],
                [
                    InlineKeyboardButton("👑 Vɪsɪᴏɴ Iᴀs", callback_data="vision_ias_"),
                    InlineKeyboardButton("👑 Eᴠᴇʀᴇsᴛ Iᴍᴘᴀᴄᴛ", callback_data="everest_impact")
                ],
                [
                    InlineKeyboardButton("👑 Vɪᴅʏᴀɢʀᴀᴍ", callback_data="vidyagram_"),
                    InlineKeyboardButton("👑 Rᴀɴᴋᴇʀs Gᴜʀᴜᴋᴜʟ", callback_data="maintainer_")
                ],
                [
                    InlineKeyboardButton("𝐁 𝐀 𝐂 𝐊", callback_data="modes_")
                ]
                ]


button2 = [
                [
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),   
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),   
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),              
                ],
                [
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),   
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),   
                ],
                [
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),   
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),       
                ],
                [
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),   
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),       
                ],
                [
                    InlineKeyboardButton("﹤", callback_data="manual_"),
                    InlineKeyboardButton("ʙ ᴀ ᴄ ᴋ", callback_data="modes_"),
                    InlineKeyboardButton("﹥", callback_data="next_2")
                ]
                ]



button3 = [              
                [   
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [   
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [   
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [              
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [
                    InlineKeyboardButton("﹤", callback_data="next_1"),
                    InlineKeyboardButton("ʙ ᴀ ᴄ ᴋ", callback_data="modes_"),
                    InlineKeyboardButton("﹥", callback_data="next_3")
                ]
                ]



button4 = [              
                [   
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [   
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [   
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                ],
                [
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [              
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [
                    InlineKeyboardButton("﹤", callback_data="next_2"),
                    InlineKeyboardButton("ʙ ᴀ ᴄ ᴋ", callback_data="modes_"),
                    InlineKeyboardButton("﹥", callback_data="next_4")
                ]
                ]


button5 = [              
                [   
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [   
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [   
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [              
                    InlineKeyboardButton("Soon", callback_data="maintainer_"),
                    InlineKeyboardButton("Soon", callback_data="maintainer_")
                ],
                [
                    InlineKeyboardButton("﹤", callback_data="next_3"),
                    InlineKeyboardButton("ʙ ᴀ ᴄ ᴋ", callback_data="modes_"),
                    InlineKeyboardButton("﹥", callback_data="manual_")
                ]
                ]
                


back_button  = [[
                    InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="modes_"),                    
                ]]



# ------------------------------------------------------------------------------- #

def photo():
    # Use THUMB_URL (correct case) from config
    return config.THUMB_URL

    # Keeping the old code as comment for reference

@app.on_message(filters.command("start"))  # & filters.user(SUDO_USERS))
async def start(_, message):
    join = await subscribe(_, message)
    if join == 1:
        return
    try:
        await message.reply_photo(
            photo=photo(),
            caption=script.START_TXT.format(message.from_user.mention),
            reply_markup=buttons
        )
    except Exception as e:
        print(f"Error in start command: {e}")
        try:
            local_photo = "Extractor/thumbs/txt-5.jpg" if os.path.exists("Extractor/thumbs/txt-5.jpg") else "thumb.jpg"
            if os.path.exists(local_photo):
                await message.reply_photo(
                    photo=local_photo,
                    caption=script.START_TXT.format(message.from_user.mention),
                    reply_markup=buttons
                )
            else:
                await message.reply_text(
                    script.START_TXT.format(message.from_user.mention),
                    reply_markup=buttons
                )
        except Exception as e2:
            print(f"Fallback start error: {e2}")
            await message.reply_text(
                script.START_TXT.format(message.from_user.mention),
                reply_markup=buttons
            )

ADMIN_HELP_TEXT = """👑 <b><u>ADMIN CONTROL PANEL & HELP GUIDE</u></b> 👑

नमस्ते एडमिन! यहाँ बॉट को मैनेज करने और यूज़र्स को प्रीमियम देने की पूरी गाइड है:

━━━━━━━━━━━━━━━━━━━━━
💎 <b><u>१. यूज़र को प्रीमियम कैसे दें?</u></b>
<b>कमांड:</b> <code>/add_premium &lt;user_id&gt; &lt;time&gt;</code>

<b>उदाहरण (Examples):</b>
• <code>/add_premium 1234567890 30 days</code> (१ महीने के लिए)
• <code>/add_premium 1234567890 1 month</code>
• <code>/add_premium 1234567890 7 days</code> (१ हफ्ते के लिए)
• <code>/add_premium 1234567890 1 year</code> (१ साल के लिए)
• <code>/add_premium 1234567890 2 hours</code> (टेस्टिंग के लिए)

⚡ <b>शॉर्टकट (Direct Reply):</b>
अगर किसी यूज़र का मैसेज आया है, तो उसके मैसेज पर <b>Reply</b> करें और सिर्फ लिखें:
👉 <code>/add_premium 30 days</code>
<i>(बॉट अपने आप यूज़र की ID ले लेगा और उसे तुरंत प्रीमियम दे देगा)</i>

━━━━━━━━━━━━━━━━━━━━━
🆔 <b><u>२. यूज़र ID कैसे निकालें?</u></b>
• किसी के भी मैसेज पर Reply करके <code>/id</code> भेजें।
• खुद की ID देखने के लिए सीधे <code>/id</code> भेजें।

━━━━━━━━━━━━━━━━━━━━━
🔍 <b><u>३. प्रीमियम स्टेटस कैसे चेक करें?</u></b>
• <code>/chk_premium 1234567890</code>
<i>(या यूज़र के मैसेज पर Reply करके <code>/chk_premium</code> भेजें)</i>

━━━━━━━━━━━━━━━━━━━━━
❌ <b><u>४. प्रीमियम कैसे हटाएं (Revoke)?</u></b>
• <code>/remove_premium 1234567890</code>
<i>(या Reply करके <code>/remove_premium</code> भेजें)</i>

━━━━━━━━━━━━━━━━━━━━━
📋 <b><u>५. सभी एक्टिव प्रीमियम यूज़र्स की लिस्ट:</u></b>
• <code>/premium_users</code>

━━━━━━━━━━━━━━━━━━━━━
📢 <b><u>६. ब्रॉडकास्ट (सभी यूज़र्स को मैसेज भेजना):</u></b>
• किसी भी मैसेज/फोटो पर Reply करके <code>/broadcast</code> भेजें।

━━━━━━━━━━━━━━━━━━━━━
📊 <b><u>७. बॉट स्टेट्स (Stats):</u></b>
• <code>/stats</code> (कुल यूज़र्स और सर्वर स्थिति)
━━━━━━━━━━━━━━━━━━━━━"""

@app.on_message(filters.command(["adminhelp", "admin_help"]))
async def admin_help_cmd(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply_text("⛔️ <b>Access Denied!</b>\nयह कमांड केवल बॉट एडमिन के लिए है।")
    await message.reply_text(ADMIN_HELP_TEXT, disable_web_page_preview=True)

@app.on_message(filters.command("help"))
async def help_cmd(client, message):
    if is_admin(message.from_user.id):
        return await message.reply_text(ADMIN_HELP_TEXT, disable_web_page_preview=True)
    user_help_text = (
        "📚 <b><u>DREAM EXTRACTOR BOT HELP</u></b> 📚\n\n"
        "इस बॉट से आप विभिन्न कोचिंग पोर्टल्स के कोर्सेज एक्सट्रैक्ट कर सकते हैं:\n\n"
        "⚡ <b>उपलब्ध कमांड्स:</b>\n"
        "• /start - मेनू और ऐप्स लिस्ट देखें\n"
        "• /myplan - अपना एक्टिव प्रीमियम प्लान देखें\n"
        "• /plans - प्रीमियम प्लान्स और प्राइजिंग देखें\n"
        "• /vidyagram - Vidyagram (AR Maths) कोर्सेज\n"
        "• /freeappx - Appx कोर्सेज लिस्ट\n"
        "• /freepw - Physics Wallah कोर्सेज\n"
        "• /freecp - Classplus कोर्सेज\n\n"
        f"👑 प्रीमियम एक्सेस लेने या सहायता के लिए एडमिन से संपर्क करें: @{ADMIN_BOT_USERNAME}"
    )
    await message.reply_text(user_help_text, disable_web_page_preview=True)

@app.on_message(filters.command(["vidyagram", "vidyagram_txt"]))
async def vidyagram_cmd(client, message):
    api = "armathsapi.akamai.net.in"
    name = "Vidyagram"
    await appex_v5_txt(app, message, api, name)

@app.on_callback_query(filters.regex("^appxlist$"))
async def show_alphabet(client, query):
    keyboard = get_alphabet_keyboard()
    await query.message.edit_text("𝐒𝐞𝐥𝐞𝐜𝐭 𝐀 𝐋𝐞𝐭𝐭𝐞𝐫 𝐓𝐨 𝐕𝐢𝐞𝐰 𝐀𝐩𝐩𝐬 ✨", reply_markup=keyboard)

@app.on_callback_query(filters.regex("^alpha_"))
async def show_apps_for_letter(client, query):
    letter = query.data.split('_')[1]
    apps = get_apps_by_letter(letter)
    
    if not apps:
        await query.answer(f"No apps found starting with {letter}", show_alert=True)
        return
    
    keyboard, total_pages = create_app_keyboard(apps, page=0, letter=letter)
    # Create header with total apps count and page info
    text = f"📱 𝐀𝐩𝐩𝐬 𝐒𝐭𝐚𝐫𝐭𝐢𝐧𝐠 𝐖𝐢𝐭𝐡 '{letter}' ({len(apps)} apps)\n"
    text += f"𝐏𝐚𝐠𝐞: 1/{total_pages}\n"
    text += "═══════════════════"
    
    try:
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        print(f"Error showing apps: {e}")
        await query.answer("Error displaying apps. Please try again.", show_alert=True)

@app.on_callback_query(filters.regex("^page_"))
async def handle_pagination(client, query):
    try:
        # New format: page_LETTER_PAGENUMBER
        _, letter, page = query.data.split('_')
        page = int(page)
        
        apps = get_apps_by_letter(letter)
        if not apps:
            await query.answer("No apps found", show_alert=True)
            return
            
        keyboard, total_pages = create_app_keyboard(apps, page, letter)
        
        # Update header with new page number
        text = f"📱 𝐀𝐩𝐩𝐬 𝐒𝐭𝐚𝐫𝐭𝐢𝐧𝐠 𝐖𝐢𝐭𝐡 '{letter}' ({len(apps)} apps)\n"
        text += f"𝐏𝐚𝐠𝐞: {page + 1}/{total_pages}\n"
        text += "═══════════════════"
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        print(f"Pagination error: {e}")
        await query.answer("Error in pagination. Please try again.", show_alert=True)

@app.on_callback_query(filters.regex("^app_"))
async def handle_app_selection(client, query):
    try:
        app_name = query.data.split("_")[1]
        with open('appxapis.json', 'r', encoding='utf-8') as f:
            apps = json.load(f)
            
        # Find the selected app
        selected_app = next((app for app in apps if app['name'] == app_name), None)
        
        if selected_app:
            api = selected_app['api']
            name = selected_app['name']
            # Remove https:// if present
            api = api.replace("https://", "").replace("http://", "")
            
            # Use appex_v5_txt for handling the API call
            await appex_v5_txt(app, query.message, api, name)
        else:
            await query.message.edit_text(
                "**Error: App not found**\n\n"
                "Please try selecting another app.",
                reply_markup=get_alphabet_keyboard()
            )
    except Exception as e:
        await query.message.edit_text(
            f"**Error processing app: {str(e)}**\n\n"
            "Please try again later.",
            reply_markup=get_alphabet_keyboard()
        )

async def process_with_timeout(func, client, message, user_id, timeout=60):
    try:
        return await asyncio.wait_for(func(client, message, user_id), timeout=timeout)
    except asyncio.TimeoutError:
        return "timeout"
    except Exception as e:
        print(f"Error in process_with_timeout: {e}")
        return f"error:{str(e)}"

@app.on_callback_query(filters.regex("^pwwp$"))
async def pwwp_callback(client, callback_query):
    try:
        # Send initial processing message
        processing_msg = await callback_query.message.reply_text(
            "⏳ Starting process... Please wait  - **DONT LOGIN WITH PHONE NUMBER, It Leads to ban your account of PW**"
        )
        
        user_id = callback_query.from_user.id
        
        try:
            # Process directly without timeout
            await process_pwwp(client, callback_query.message, user_id)
        except Exception as e:
            await processing_msg.edit_text(
                f"❌ An error occurred: {str(e)}\n"
                "Please try again."
            )
            
    except Exception as e:
        print(f"Error in pwwp_callback: {e}")
        await callback_query.answer("An error occurred", show_alert=True)

@app.on_callback_query(filters.regex("^appxwp$"))
async def appxwp_callback(client, callback_query):
    try:
        # Send initial processing message
        processing_msg = await callback_query.message.reply_text(
            "⏳ Starting process... Please wait"
        )
        
        user_id = callback_query.from_user.id
        
        try:
            # Process directly using processing_msg
            await process_appxwp(client, processing_msg, user_id)
        except Exception as e:
            await processing_msg.edit_text(
                f"❌ An error occurred: {str(e)}\n"
                "Please try again."
            )
            
    except Exception as e:
        print(f"Error in appxwp_callback: {e}")
        await callback_query.answer("An error occurred", show_alert=True)

@app.on_callback_query(filters.regex("^cpwp$"))
async def cpwp_callback(client, callback_query):
    try:
        # Send initial processing message
        processing_msg = await callback_query.message.reply_text(
            "⏳ Starting process... Please wait"
        )
        
        user_id = callback_query.from_user.id
        
        try:
            # Process directly without timeout
            await process_cpwp(client, callback_query.message, user_id)
        except Exception as e:
            await processing_msg.edit_text(
                f"❌ An error occurred: {str(e)}\n"
                "Please try again."
            )
            
    except Exception as e:
        print(f"Error in cpwp_callback: {e}")
        await callback_query.answer("An error occurred", show_alert=True)

@app.on_callback_query(filters.regex("^cw$"))
async def career_will_callback(app: Client, callback_query: CallbackQuery):
    try:
        await callback_query.answer()
        processing_msg = await callback_query.message.reply_text("Starting CareerWill extractor...")
        await career_will(app, callback_query.message)
        try:
            await processing_msg.delete()
        except:
            pass
    except Exception as e:
        await callback_query.message.reply_text(f"Error: {str(e)}")

async def edit_msg(query, text, reply_markup=None):
    try:
        if query.message.photo or query.message.caption:
            await query.message.edit_caption(caption=text, reply_markup=reply_markup)
        else:
            await query.message.edit_text(text=text, reply_markup=reply_markup)
    except Exception:
        try:
            await query.message.edit_text(text=text, reply_markup=reply_markup)
        except Exception:
            await query.message.reply_text(text=text, reply_markup=reply_markup)

@app.on_callback_query()
async def handle_callback(client, query):
    
    if query.data=="home_":        
        await edit_msg(
              query,
              script.START_TXT.format(query.from_user.mention),
              reply_markup=buttons
            )

    elif query.data == "admin_help_btn":
        user_id = query.from_user.id
        if not is_admin(user_id):
            await query.answer("⛔️ यह बटन केवल बॉट एडमिन के लिए है!", show_alert=True)
            return

        await query.answer("👑 Welcome Admin!")
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 ʀᴇꜰʀᴇsʜ", callback_data="admin_help_btn")],
            [InlineKeyboardButton("⬅️ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ", callback_data="home_")]
        ])
        await edit_msg(query, ADMIN_HELP_TEXT, reply_markup=reply_markup)

    elif query.data == "master_appx_menu":
        text = (
            "👑 <b>MASTER APPX MENU</b> 👑\n\n"
            "• <b>APPX LIST</b> - Browse apps by name (A-Z)\n"
            "• <b>APPX OTP</b> - Generate OTP for apps\n"
            "• <b>APPX API</b> - Find API endpoints\n"
            "• <b>MANUAL API ENTRY</b> - Enter API directly\n"
            "• <b>TEXT ⟷ HTML</b> - Convert TXT and HTML files"
        )
        await edit_msg(query, text, reply_markup=master_appx_buttons)

    elif query.data == "appx_otp":
        await query.answer()
        await send_otpp(app, query.message)

    elif query.data == "manual_api_entry":
        await query.answer()
        await appex_v4_txt(app, query.message)

    elif query.data == "view_plans_cmd":
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ", url=f"https://t.me/{ADMIN_BOT_USERNAME}")],
            [InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data="home_")]
        ])
        await edit_msg(query, script.PLANS_TXT, reply_markup=reply_markup)
     
    elif query.data=="modes_":
        reply_markup = InlineKeyboardMarkup(modes_button)
        await edit_msg(query, script.MODES_TXT, reply_markup=reply_markup)
        
    elif query.data=="custom_":        
        user_id = query.from_user.id
        if not await check_user_is_premium(user_id):
            await query.answer("⚠️ यह फीचर केवल प्रीमियम यूज़र्स के लिए है!", show_alert=True)
            text = (
                "🔒 <b>﹝𝐖 𝐈 𝐓 𝐇 𝐎 𝐔 𝐓  𝐋 𝐎 𝐆 𝐈 𝐍﹞</b>\n\n"
                "⚠️ <b>यह फीचर केवल प्रीमियम यूज़र्स के लिए उपलब्ध है!</b>\n\n"
                "Without Login मोड में आप बिना आईडी-पासवर्ड के सीधे लिंक से कोर्सेस एक्सट्रैक्ट कर सकते हैं।\n\n"
                f"👑 प्रीमियम एक्सेस लेने के लिए एडमिन से संपर्क करें:\n"
                f"👉 @{ADMIN_BOT_USERNAME}\n\n"
                "या प्लान्स देखने के लिए /plans टाइप करें।"
            )
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 ᴠɪᴇᴡ ᴘʟᴀɴs", callback_data="view_plans_cmd")],
                [InlineKeyboardButton("📞 ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ", url=f"https://t.me/{ADMIN_BOT_USERNAME}")],
                [InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data="home_")]
            ])
            await edit_msg(query, text, reply_markup=reply_markup)
            return

        reply_markup = InlineKeyboardMarkup(custom_button)
        await edit_msg(query, script.CUSTOM_TXT, reply_markup=reply_markup)
        
    elif query.data=="manual_":        
        reply_markup = InlineKeyboardMarkup(button1)
        await edit_msg(query, script.MANUAL_TXT, reply_markup=reply_markup)

    # Appex List Handler
    elif query.data=="appxlist":
        keyboard = get_alphabet_keyboard()
        await query.message.edit_text("𝐒𝐞𝐥𝐞𝐜𝐭 𝐀 𝐋𝐞𝐭𝐭𝐞𝐫 𝐓𝐨 𝐕𝐢𝐞𝐰 𝐀𝐩𝐩𝐬 ✨", reply_markup=keyboard)

    # Alphabet Selection Handler
    elif query.data.startswith("alpha_"):
        letter = query.data.split("_")[1]
        try:
            with open('appxapis.json', 'r', encoding='utf-8') as f:
                apps = json.load(f)
            
            # Filter apps starting with the selected letter
            filtered_apps = [app for app in apps if app['name'].lower().startswith(letter.lower())]
            
            if not filtered_apps:
                await query.message.edit_text(
                    f"**No apps found starting with '{letter}'**\n\n"
                    "Please select another letter.",
                    reply_markup=get_alphabet_keyboard()
                )
                return
                
            keyboard, total_pages = create_app_keyboard(filtered_apps, 0, letter)
            await query.message.edit_text(
                f"**Apps starting with '{letter}'**\n\n"
                "Select an app to proceed:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            await query.message.edit_text(
                f"**Error loading apps: {str(e)}**\n\n"
                "Please try again later.",
                reply_markup=get_alphabet_keyboard()
            )

    # Page Navigation Handler
    elif query.data.startswith("page_"):
        try:
            parts = query.data.split("_")
            letter = parts[1]
            page = int(parts[2])
            
            with open('appxapis.json', 'r', encoding='utf-8') as f:
                apps = json.load(f)
                
            filtered_apps = [app for app in apps if app['name'].lower().startswith(letter.lower())]
            keyboard, total_pages = create_app_keyboard(filtered_apps, page, letter)
            
            await query.message.edit_text(
                f"**Apps starting with '{letter}'**\n\n"
                "Select an app to proceed:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            await query.message.edit_text(
                f"**Error loading page: {str(e)}**\n\n"
                "Please try again later.",
                reply_markup=get_alphabet_keyboard()
            )

    # Coaching-specific handlers
    elif query.data == "perfect_acc":     
        api = "perfectionacademyapi.appx.co.in"
        name = "Perfection Academy"
        await appex_v5_txt(app, query.message, api, name)
      
    
      
    elif query.data == "e1_coaching":     
        api = "e1coachingcenterapi.classx.co.in"
        name = "e1 coaching"
        await appex_v5_txt(app, query.message, api, name)
      
    elif query.data == "samyak_ras":     
        api = "samyakapi.classx.co.in"
        name = "Samyak"
        await appex_v5_txt(app, query.message, api, name)
      
    elif query.data == "vj_education":     
        api = "vjeducationapi.appx.co.in"
        name = "VJ Education"
        await appex_v5_txt(app, query.message, api, name)
      
    elif query.data == "gyan_bindu":     
        api = "gyanbinduapi.appx.co.in"
        name = "Gyan Bindu"
        await appex_v5_txt(app, query.message, api, name)
      
    elif query.data == "dhananjay_ias":     
        api = "dhananjayiasacademyapi.classx.co.in"
        name = "Dhananjay IAS"
        await appex_v5_txt(app, query.message, api, name)
      
    elif query.data == "think_ssc":     
        api = "thinksscapi.classx.co.in"
        name = "Think SSC"
        await appex_v5_txt(app, query.message, api, name)
      
    elif query.data == "note_book":     
        api = "notebookapi.classx.co.in"
        name = "Note Book"
        await appex_v5_txt(app, query.message, api, name)
      
    elif query.data == "uc_live":     
        api = "ucliveapi.classx.co.in"
        name = "UC LIVE"
        await appex_v5_txt(app, query.message, api, name)
      
    elif query.data == "space_ias":     
        api = "spaceiasapi.classx.co.in"
        name = "Space IAS"
        await appex_v5_txt(app, query.message, api, name)
      
    elif query.data == "rg_vikramjeet":     
        api = "rgvikramjeetapi.classx.co.in"
        name = "RG Vikramjeet"
        await appex_v5_txt(app, query.message, api, name)
      
    elif query.data == "vidya_bihar":     
        api = "vidyabiharapi.teachx.in"
        name = "Vidya Vihar"
        await appex_v5_txt(app, query.message, api, name)
      
    elif query.data == "aman_sir":     
        api = "amansirenglishapi.classx.co.in"
        name = "Aman Sir English"
        await appex_v5_txt(app, query.message, api, name)
      
    elif query.data == "nirman_ias":     
        api = "nirmaniasapi.classx.co.in"
        name = "Nirman IAS"
        await appex_v5_txt(app, query.message, api, name)
      
    elif query.data == "permar_ssc":     
        api = "parmaracademyapi.classx.co.in"
        name = "Parmar Academy"
        await appex_v5_txt(app, query.message, api, name)
      
    elif query.data == "neo_spark":     
        api = "neosparkapi.classx.co.in"
        name = "Neo Spark"
        await appex_v5_txt(app, query.message, api, name)
      
    elif query.data == "md_classes":     
        api = "mdclassesapi.classx.co.in"
        name = "MD Classes"
        await appex_v5_txt(app, query.message, api, name)
      
    elif query.data == "ng_learners":     
        api = "nglearnersapi.classx.co.in"
        name = "NG Learners"
        await appex_v5_txt(app, query.message, api, name)

    elif query.data == "anilsir_iti":
        api = "anilsiritiapi.classx.co.in"
        name = "Anil Sir Iti"
        await appex_v5_txt(app, query.message, api, name) 

    elif query.data == "education_adda":
        api = "educationaddaplusapi.classx.co.in"
        name = "Education Adda Plus"
        await appex_v5_txt(app, query.message, api, name) 

    elif query.data == "achievers_acc":
        api = "achieversacademyapi.classx.co.in"
        name = "Achievers Academy"
        await appex_v5_txt(app, query.message, api, name) 

    elif query.data == "commando_acc":
        api = "commandoacademyapi.appx.co.in"
        name = "Commando Academy"
        await appex_v5_txt(app, query.message, api, name) 

    elif query.data == "neet_kakajee":
        api = "neetkakajeeapi.classx.co.in"
        name = "Neet Kaka JEE"
        await appex_v5_txt(app, query.message, api, name) 

    elif query.data == "everest_impact":
        api = "everestimpactapi.classx.co.in"
        name = "Everest Impact"
        await appex_v5_txt(app, query.message, api, name) 

    elif query.data == "vidyagram_":
        api = "armathsapi.akamai.net.in"
        name = "Vidyagram"
        await appex_v5_txt(app, query.message, api, name) 

    elif query.data == "app_exampur":
        api = "exampurapi.classx.co.in"
        name = "App Exampur"
        await appex_v5_txt(app, query.message, api, name)

    elif query.data=="classplus_":          
        await classplus_txt(app, query.message)

    elif query.data == 'ak_':
        await ak_start(client, query.message)
  
    elif query.data == 'pw2_':
        await query.message.reply_text(
            "**CHHOSE FROM BELOW **",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Mobile No.", callback_data='mobile_'),
                    InlineKeyboardButton("Token", callback_data='token_'),
                ]]))

    elif query.data == 'mobile_':
        await pw_mobile(app, query.message)

    elif query.data == 'token_':
        await pw_token(app, query.message)
        



  

  

    elif query.data=="close_data":
        await query.message.delete()
        await query.message.reply_to_message.delete()

    elif query.data == "txt2html_":
        await show_txt2html_help(client, query.message)

    elif query.data == "converter_":
        await query.message.edit_text(
            "**🔄 File Conversion Tools**\n\n"
            "**<blockquote>Choose the conversion type you need:</blockquote>**\n\n"
            "• 📝 **Text to HTML**: Convert text files to beautiful HTML pages\n"
            "• 📄 **HTML to Text**: Extract links from HTML files back to text",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📝 Tᴇxᴛ ᴛᴏ HTML", callback_data="txt2html_"),
                    InlineKeyboardButton("📄 HTML ᴛᴏ Tᴇxᴛ", callback_data="html2txt_")
                ],
                [
                    InlineKeyboardButton("𝐁 𝐀 𝐂 𝐊", callback_data="home_")
                ]
            ])
        )

    elif query.data == "html2txt_":
        await query.message.edit_text(
            "**📄 HTML to Text Converter**\n\n"
            "**<blockquote>Convert HTML files back to text format with decoded URLs.</blockquote>**\n\n"
            "**How to use:**\n"
            "• Send an HTML file directly\n"
            "• Or use command `/html2txt` with HTML file\n"
            "• Get back a text file with all extracted links\n\n"
            "**Features:**\n"
            "• Extracts all video links\n"
            "• Extracts all PDF links\n"
            "• Decodes obfuscated URLs\n"
            "• Clean name:url format",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("𝐁 𝐀 𝐂 𝐊", callback_data="converter_")
                ]
            ])
        )

    elif query.data == "maintainer_":
        await query.message.edit_text("THIS FEATURE IS UNDER DEVELOPMENT")
    # Coaching login handlers
    elif query.data == "utkarsh_":
    
        await handle_utk_logic(app, query.message)
 

    
    elif query.data == "pw_":
        await pw_login(app, query.message)
    elif query.data == "rgvikramjeet_":
        await rgvikramjeet(app, query.message)
    elif query.data == "ugcw_":
        await career_will(app, query.message)
    elif query.data == "vision_ias_":
        await scrape_vision_ias(app, query.message)
    elif query.data == "my_pathshala_":
        await my_pathshala_login(app, query.message)
    elif query.data == "khan_":
        await khan_login(app, query.message)
    elif query.data == "kdlive_":
        await kdlive(app, query.message)
    elif query.data == "iq_":
        await handle_iq_logic(app, query.message)
    elif query.data == "adda_":
        await adda_command_handler(app, query.message)
    elif query.data == "classplus_":
        await classplus_txt(app, query.message)
    elif query.data == "ak_":
        await ak_start(app, query.message)
    elif query.data == "exampur_txt":
        await exampur_txt(app, query.message)
    elif query.data == "guidely_":
        await guidely_login(app, query.message)
    elif query.data == "oliveboard_":
        await oliveboard_login(app, query.message)
    elif query.data == "testbook_":
        await testbook_handler(app, query.message)

def get_alphabet_keyboard():
    """Create a keyboard with A-Z buttons in a modern style"""
    alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    keyboard = []
    row = []
    
    for letter in alphabet:
        row.append(InlineKeyboardButton(f"{letter}", callback_data=f"alpha_{letter}"))
        if len(row) == 7:  # 7 buttons per row for better layout
            keyboard.append(row)
            row = []
    
    if row:  # Add any remaining buttons
        keyboard.append(row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("𝐁 𝐀 𝐂 𝐊", callback_data="home_")])
    
    return InlineKeyboardMarkup(keyboard)

def get_apps_by_letter(letter):
    """Get apps starting with the given letter from appxapis.json"""
    try:
        with open('appxapis.json', 'r') as f:
            apps = json.load(f)
        
        # Filter apps starting with the letter
        filtered_apps = [app for app in apps if app['name'].upper().startswith(letter)]
        
        # Sort alphabetically
        filtered_apps.sort(key=lambda x: x['name'])
        
        return filtered_apps
    except Exception as e:
        print(f"Error reading appxapis.json: {e}")
        return []


def to_small_caps(text):
    normal = "abcdefghijklmnopqrstuvwxyz"
    small_caps = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    table = str.maketrans(''.join(normal), ''.join(small_caps))
    return text.lower().translate(table)


def create_app_keyboard(apps, page=0, letter=None):
    """Create a keyboard with app buttons, 40 apps per page"""
    keyboard = []
    row = []
    
    # Calculate pagination
    items_per_page = 40
    total_pages = (len(apps) + items_per_page - 1) // items_per_page
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(apps))
    current_apps = apps[start_idx:end_idx]
    
    # Add app buttons
    for idx, app in enumerate(current_apps):
        name = app['name']
        # Clean up the name and ensure proper spacing
        styled_name = name.replace("api", "").replace("Api", "")  # Remove api/Api from name
        styled_name = ' '.join(word.capitalize() for word in styled_name.split())  # Proper capitalization

        # Create button with crown emoji and proper spacing
        button_text = f"👑 {styled_name}"
        button = InlineKeyboardButton(button_text, callback_data=f"app_{name}")
        row.append(button)
        
        
        # Always use 2 buttons per row
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    # Handle any remaining buttons in the last row
    if row:
        if len(row) == 1:
            row.append(InlineKeyboardButton(" ", callback_data="ignore"))
        keyboard.append(row)
    
    # Add navigation row
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("« Prev", callback_data=f"page_{letter}_{page-1}"))
    nav_row.append(InlineKeyboardButton("« 𝐁𝐚𝐜𝐤 »", callback_data="appxlist"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next »", callback_data=f"page_{letter}_{page+1}"))
    keyboard.append(nav_row)
    
    return keyboard, total_pages

@app.on_callback_query(filters.regex("^ignore$"))
async def handle_ignore(client, query):
    await query.answer()

def setup(app: Client):
    """Setup the start module"""
    app.add_handler(filters.command("start"), start_command)
    app.add_handler(filters.callback_query(), handle_callback_query)
    
    # Setup message handlers for AKExtractor
    app.add_handler(filters.private & ~filters.command, ak_extractor.handle_message)

@app.on_message(filters.command("txt2html"))
async def txt2html_command(client, message):
    await show_txt2html_help(client, message)

@app.on_message(filters.private & filters.document)
async def handle_document(client, message):
    """Handle document messages"""
    if message.document.file_name.endswith('.txt'):
        await handle_txt2html(client, message)
    elif message.document.file_name.endswith('.html'):
        await html_to_text_command(client, message)

def deobfuscate_url(encoded_url):
    """Deobfuscate URL back to original form."""
    try:
        # Double decode
        decoded = base64.b64decode(encoded_url.encode()).decode()
        decoded = base64.b64decode(decoded.encode()).decode()
        # Remove salt (first 8 characters)
        return decoded[8:]
    except:
        return encoded_url

async def fetch_url(session, url):
    """Fetch URL from API asynchronously and extract actual URL."""
    try:
        if 'api.extractor.workers.dev' in url:
            # Extract URL from the API URL if it's in the format
            url_param = re.search(r'url=([^&]+)', url)
            if url_param:
                return url_param.group(1)
            # If not in URL, try fetching from API
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'url' in data:
                        return data['url']
    except:
        pass
    return url

@app.on_message(filters.command("html2txt"))
async def html_to_text_command(client: Client, message: Message):
    """Convert HTML file back to text format."""
    try:
        # Check if file is in reply or direct message
        if message.reply_to_message and message.reply_to_message.document:
            doc = message.reply_to_message.document
            is_reply = True
        elif message.document:
            doc = message.document
            is_reply = False
        else:
            await message.reply_text("Please send an HTML file or reply to one.")
            return
            
        # Check if it's an HTML file
        if not doc.file_name.endswith('.html'):
            await message.reply_text("Please send an HTML file only.")
            return
            
        # Download the file
        progress_msg = await message.reply_text("Processing HTML file...")
        if is_reply:
            file_path = await message.reply_to_message.download()
        else:
            file_path = await message.download()
        
        # Read and parse HTML
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Create aiohttp session for async requests
        async with aiohttp.ClientSession() as session:
            # Extract video links
            video_links = []
            tasks = []
            video_names = []
            
            for div in soup.find_all('div', class_='list-group-item'):
                onclick = div.get('onclick', '')
                if 'playVideo' in onclick:
                    encoded_url = re.search(r"playVideo\('([^']+)'\)", onclick)
                    if encoded_url:
                        url = deobfuscate_url(encoded_url.group(1))
                        name = div.find('span').text.strip()
                        if 'api.extractor.workers.dev' in url:
                            tasks.append(fetch_url(session, url))
                            video_names.append(name)
                        else:
                            # For non-API URLs, check if it contains url= parameter
                            url_param = re.search(r'url=([^&]+)', url)
                            if url_param:
                                url = url_param.group(1)
                            video_links.append((name, url))
            
            # Wait for all API requests to complete
            if tasks:
                results = await asyncio.gather(*tasks)
                for name, url in zip(video_names, results):
                    video_links.append((name, url))
                
            # Extract PDF links
            pdf_links = []
            for div in soup.find_all('div', class_='list-group-item'):
                view_btn = div.find('button', class_='view')
                if view_btn and 'viewPDF' in view_btn.get('onclick', ''):
                    encoded_url = re.search(r"viewPDF\('([^']+)'\)", view_btn['onclick'])
                    if encoded_url:
                        url = deobfuscate_url(encoded_url.group(1))
                        # Check for url= parameter
                        url_param = re.search(r'url=([^&]+)', url)
                        if url_param:
                            url = url_param.group(1)
                        name = div.find('span').text.strip()
                        pdf_links.append((name, url))
                    
            # Extract other links
            other_links = []
            for div in soup.find_all('div', class_='list-group-item'):
                link = div.find('a', onclick=True)
                if link and 'deobfuscateUrl' in link.get('onclick', ''):
                    encoded_url = re.search(r"deobfuscateUrl\('([^']+)'\)", link['onclick'])
                    if encoded_url:
                        url = deobfuscate_url(encoded_url.group(1))
                        # Check for url= parameter
                        url_param = re.search(r'url=([^&]+)', url)
                        if url_param:
                            url = url_param.group(1)
                        name = div.find('span').text.strip()
                        other_links.append((name, url))

        # Create text content
        text_content = "🎥 Videos:\n"
        for name, url in video_links:
            # URL decode the final URL
            url = requests.utils.unquote(url)
            text_content += f"{name}:{url}\n"
            
        if pdf_links:
            text_content += "\n📄 PDFs:\n"
            for name, url in pdf_links:
                url = requests.utils.unquote(url)
                text_content += f"{name}:{url}\n"
                
        if other_links:
            text_content += "\n🔗 Other Links:\n"
            for name, url in other_links:
                url = requests.utils.unquote(url)
                text_content += f"{name}:{url}\n"
                
        text_content += "\n@GodxBots"
                
        # Save as text file
        txt_path = file_path.rsplit('.', 1)[0] + '.txt'
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"IMAGE: {TXT_LOGO_URL}\n\n" + text_content)
            
        doc_thumb = "Extractor/thumbs/txt-5.jpg" if os.path.exists("Extractor/thumbs/txt-5.jpg") else (thumb_path if thumb_path else None)
        # Send the text file
        try:
            await message.reply_document(
                txt_path,
                thumb=doc_thumb,
                caption="<blockquote>✅ HTML converted to text format\n🔓 All URLs have been decoded\n\n🤖 @GodxBots</blockquote>"
            )
        finally:
            # Cleanup
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            if os.path.exists(txt_path):
                try:
                    os.remove(txt_path)
                except:
                    pass
        await progress_msg.delete()
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")



    

    
