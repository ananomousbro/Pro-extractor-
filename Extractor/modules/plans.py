import re
from datetime import timedelta
import pytz
import datetime, time
from Extractor import app
from config import PREMIUM_LOGS, OWNER_ID, ADMINS
from Extractor.core.func import get_seconds
from Extractor.core.mongo import plans_db  
from pyrogram import filters 
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong


def is_admin(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in ADMINS


@app.on_message(filters.command("id"))
async def get_id_cmd(client, message):
    if message.reply_to_message:
        replied = message.reply_to_message.from_user
        if replied:
            text = (
                f"👤 <b>Replied User ID:</b> <code>{replied.id}</code>\n"
                f"👤 <b>Name:</b> {replied.mention}\n\n"
                f"🆔 <b>Your ID:</b> <code>{message.from_user.id}</code>\n"
                f"💬 <b>Chat ID:</b> <code>{message.chat.id}</code>"
            )
        else:
            text = (
                f"🆔 <b>Your ID:</b> <code>{message.from_user.id}</code>\n"
                f"💬 <b>Chat ID:</b> <code>{message.chat.id}</code>"
            )
    else:
        text = (
            f"🆔 <b>Your ID:</b> <code>{message.from_user.id}</code>\n"
            f"💬 <b>Chat ID:</b> <code>{message.chat.id}</code>"
        )
    await message.reply_text(text)


@app.on_message(filters.command("remove_premium"))
async def remove_premium_handler(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply_text("⛔️ <b>Only Bot Admin can use this command!</b>")

    user_id = None
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    elif len(message.command) >= 2:
        try:
            user_id = int(message.command[1])
        except ValueError:
            return await message.reply_text("❌ <b>Invalid User ID!</b>\nUsage: <code>/remove_premium user_id</code>")

    if not user_id:
        return await message.reply_text("⚠️ <b>Usage:</b>\n• <code>/remove_premium user_id</code>\n• Or reply to user's message with <code>/remove_premium</code>")

    data = await plans_db.check_premium(user_id)
    if data and data.get("_id"):
        await plans_db.remove_premium(user_id)
        await message.reply_text(f"✅ <b>User <code>{user_id}</code> removed from Premium successfully!</b>")
        try:
            await client.send_message(
                chat_id=user_id,
                text="<b>ʜᴇʏ,\n\nʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ.\nᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴜsɪɴɢ ᴏᴜʀ sᴇʀᴠɪᴄᴇ 😊.</b>"
            )
        except Exception:
            pass
    else:
        await message.reply_text("❌ <b>User not found in premium database or already free!</b>")


@app.on_message(filters.command("myplan"))
async def myplan(client, message):
    user_id = message.from_user.id
    user = message.from_user.mention
    
    if user_id == OWNER_ID:
        return await message.reply_text(
            f"👑 <b>Admin Plan Data:</b>\n\n"
            f"👤 <b>User:</b> {user}\n"
            f"⚡ <b>User ID:</b> <code>{user_id}</code>\n"
            f"♾ <b>Plan:</b> LIFETIME (Bot Owner)"
        )

    data = await plans_db.check_premium(user_id)  
    if data and data.get("expire_date"):
        expiry = data.get("expire_date")
        if hasattr(expiry, "tzinfo") and expiry.tzinfo is not None:
            expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
        else:
            expiry_ist = pytz.timezone("Asia/Kolkata").localize(expiry)
            
        expiry_str = expiry_ist.strftime("%d-%m-%Y at %I:%M:%S %p")
        current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        time_left = expiry_ist - current_time

        if time_left.total_seconds() > 0:
            days = time_left.days
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_left_str = f"{days} days, {hours} hours, {minutes} mins"
            await message.reply_text(
                f"⚜️ <b>ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴅᴀᴛᴀ :</b>\n\n"
                f"👤 <b>User:</b> {user}\n"
                f"⚡ <b>User ID:</b> <code>{user_id}</code>\n"
                f"⏰ <b>Time Left:</b> {time_left_str}\n"
                f"⌛️ <b>Expiry Date:</b> {expiry_str}"
            )
        else:
            await plans_db.remove_premium(user_id)
            await message.reply_text(f"ʜᴇʏ {user},\n\nʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ ʜᴀs ᴇxᴘɪʀᴇᴅ. ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ᴛᴏ ʀᴇɴᴇᴡ.")
    else:
        await message.reply_text(f"ʜᴇʏ {user},\n\nʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ᴀɴʏ ᴀᴄᴛɪᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ.\nᴜsᴇ /plans ᴛᴏ ᴠɪᴇᴡ ᴘʀɪᴄɪɴɢ.")


@app.on_message(filters.command("chk_premium"))
async def chk_premium_handler(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply_text("⛔️ <b>Only Bot Admin can check other users!</b>")

    user_id = None
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    elif len(message.command) >= 2:
        try:
            user_id = int(message.command[1])
        except ValueError:
            return await message.reply_text("❌ <b>Invalid User ID!</b>\nUsage: <code>/chk_premium user_id</code>")

    if not user_id:
        return await message.reply_text("⚠️ <b>Usage:</b>\n• <code>/chk_premium user_id</code>\n• Or reply to user's message with <code>/chk_premium</code>")

    data = await plans_db.check_premium(user_id)  
    if data and data.get("expire_date"):
        expiry = data.get("expire_date") 
        if hasattr(expiry, "tzinfo") and expiry.tzinfo is not None:
            expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
        else:
            expiry_ist = pytz.timezone("Asia/Kolkata").localize(expiry)

        expiry_str = expiry_ist.strftime("%d-%m-%Y at %I:%M:%S %p")
        current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        time_left = expiry_ist - current_time

        if time_left.total_seconds() > 0:
            days = time_left.days
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_left_str = f"{days} days, {hours} hours, {minutes} mins"
            await message.reply_text(
                f"⚜️ <b>ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ ᴅᴀᴛᴀ :</b>\n\n"
                f"⚡ <b>User ID:</b> <code>{user_id}</code>\n"
                f"⏰ <b>Time Left:</b> {time_left_str}\n"
                f"⌛️ <b>Expiry Date:</b> {expiry_str}"
            )
        else:
            await plans_db.remove_premium(user_id)
            await message.reply_text(f"⚠️ Plan for user <code>{user_id}</code> has expired.")
    else:
        await message.reply_text(f"❌ <b>No premium data found for user ID <code>{user_id}</code> in database!</b>")


@app.on_message(filters.command("add_premium"))
async def give_premium_cmd_handler(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply_text("⛔️ <b>Only Bot Admin can give premium!</b>")

    user_id = None
    time_str = None

    # Check if replied to a user message: /add_premium 30 days
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
        if len(message.command) >= 2:
            time_str = " ".join(message.command[1:])
    elif len(message.command) >= 3:
        try:
            user_id = int(message.command[1])
            time_str = " ".join(message.command[2:])
        except ValueError:
            pass

    if not user_id or not time_str:
        return await message.reply_text(
            "📌 <b>How to Add Premium (प्रीमियम कैसे दें):</b>\n\n"
            "<b>1. यूज़र ID के साथ:</b>\n"
            "<code>/add_premium user_id time</code>\n\n"
            "<b>उदाहरण (Examples):</b>\n"
            "• <code>/add_premium 123456789 1 day</code>\n"
            "• <code>/add_premium 123456789 7 days</code>\n"
            "• <code>/add_premium 123456789 30 days</code> (या <code>1 month</code>)\n"
            "• <code>/add_premium 123456789 3 months</code>\n"
            "• <code>/add_premium 123456789 1 year</code>\n\n"
            "<b>2. यूज़र के मैसेज को Reply करके:</b>\n"
            "• <code>/add_premium 30 days</code>"
        )

    seconds = await get_seconds(time_str)
    if seconds <= 0:
        return await message.reply_text(
            "❌ <b>गलत टाइम फॉर्मेट!</b>\n"
            "कृपया इस प्रकार लिखें:\n"
            "• <code>1 day</code> या <code>30 days</code>\n"
            "• <code>1 month</code> या <code>3 months</code>\n"
            "• <code>1 year</code>\n"
            "• <code>2 hours</code>\n"
            "• <code>30 min</code>"
        )

    current_kolkata = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    joining_time_str = current_kolkata.strftime("%d-%m-%Y at %I:%M:%S %p")

    expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
    await plans_db.add_premium(user_id, expiry_time)

    expiry_kolkata = (datetime.datetime.now(pytz.timezone("Asia/Kolkata")) + datetime.timedelta(seconds=seconds)).strftime("%d-%m-%Y at %I:%M:%S %p")

    # Get user object if available
    user_mention = f"<code>{user_id}</code>"
    try:
        u = await client.get_users(user_id)
        if u:
            user_mention = u.mention
    except Exception:
        pass

    success_msg = (
        f"✅ <b>ᴘʀᴇᴍɪᴜᴍ ᴀᴅᴅᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!</b>\n\n"
        f"👤 <b>User:</b> {user_mention}\n"
        f"⚡ <b>User ID:</b> <code>{user_id}</code>\n"
        f"⏰ <b>Duration:</b> <code>{time_str}</code>\n\n"
        f"⏳ <b>Joined On:</b> {joining_time_str}\n"
        f"⌛️ <b>Expires On:</b> {expiry_kolkata}"
    )

    await message.reply_text(success_msg, disable_web_page_preview=True)

    # Send PM to user
    try:
        await client.send_message(
            chat_id=user_id,
            text=(
                f"🎉 <b>ʜᴇʏ {user_mention},</b>\n"
                f"ᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ɢᴇᴛᴛɪɴɢ ᴘʀᴇᴍɪᴜᴍ!\n\n"
                f"⏰ <b>Access:</b> <code>{time_str}</code>\n"
                f"⌛️ <b>Expires On:</b> {expiry_kolkata}\n\n"
                f"ᴇɴᴊᴏʏ ᴜɴʟɪᴍɪᴛᴇᴅ ᴇxᴛʀᴀᴄᴛɪᴏɴs! ✨"
            ),
            disable_web_page_preview=True
        )
    except Exception:
        pass

    # Send to logs
    try:
        if PREMIUM_LOGS:
            await client.send_message(
                chat_id=PREMIUM_LOGS,
                text=f"#Added_Premium\n\n" + success_msg,
                disable_web_page_preview=True
            )
    except Exception:
        pass


@app.on_message(filters.command("premium_users"))
async def premium_user_list(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply_text("⛔️ <b>Only Bot Admin can view all premium users!</b>")

    status_msg = await message.reply_text("<i>⏳ Fetching premium users from database...</i>")
    
    current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    output = "⚜️ <b>PREMIUM USERS LIST</b> ⚜️\n\n"
    count = 0

    try:
        cursor = plans_db.db.find()
        async for doc in cursor:
            uid = doc.get("_id")
            expire_date = doc.get("expire_date")
            if not expire_date:
                continue

            if hasattr(expire_date, "tzinfo") and expire_date.tzinfo is not None:
                exp_ist = expire_date.astimezone(pytz.timezone("Asia/Kolkata"))
            else:
                exp_ist = pytz.timezone("Asia/Kolkata").localize(expire_date)

            time_left = exp_ist - current_time
            if time_left.total_seconds() > 0:
                count += 1
                days = time_left.days
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                exp_str = exp_ist.strftime("%d-%m-%Y")
                output += f"{count}. <code>{uid}</code> — Expiry: {exp_str} ({days}d {hours}h left)\n"

        if count == 0:
            output = "ℹ️ No active premium users found in database."
        else:
            output = f"⚜️ <b>TOTAL PREMIUM USERS: {count}</b>\n\n" + output

        try:
            await status_msg.edit_text(output)
        except MessageTooLong:
            with open("premium_users.txt", "w") as f:
                f.write(output)
            await message.reply_document("premium_users.txt", caption="Paid Users List")
            await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Error fetching users: {e}")


@app.on_message(filters.command(["plan", "plans"]))
async def view_plans(client, message):
    from Extractor.core import script
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from config import ADMIN_BOT_USERNAME
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ", url=f"https://t.me/{ADMIN_BOT_USERNAME}")],
    ])
    await message.reply_text(script.PLANS_TXT, reply_markup=reply_markup)
