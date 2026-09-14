import time
import asyncio
import logging
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.errors import UserNotParticipant
from Extractor import app
from config import ADMINS, OWNER_ID, FSUB_CHANNELS

# Cache to store verified users: {user_id: expire_timestamp}
_verified_cache = {}
CACHE_TTL = 90  # 90 seconds cache

# Cache resolved chat IDs: {username: chat_id}
_resolved_chats = {}

JOINED_STATUSES = {"member", "administrator", "owner", "creator", "restricted"}

def is_admin(user_id: int) -> bool:
    if not user_id:
        return False
    return user_id == OWNER_ID or user_id in ADMINS

async def get_chat_id(client, username_or_id):
    if username_or_id in _resolved_chats:
        return _resolved_chats[username_or_id]
    
    target = f"@{str(username_or_id).lstrip('@')}" if isinstance(username_or_id, str) and not username_or_id.startswith("-100") else username_or_id
    try:
        chat = await client.get_chat(target)
        _resolved_chats[username_or_id] = chat.id
        return chat.id
    except Exception as e:
        logging.warning(f"[ForceSub] Could not get_chat for {target}: {e}")
        return target

async def get_missing_channels(client, user_id: int):
    if is_admin(user_id):
        return []

    now = time.time()
    if user_id in _verified_cache and _verified_cache[user_id] > now:
        return []

    missing = []
    for ch in FSUB_CHANNELS:
        try:
            target = await get_chat_id(client, ch["username"])
            member = await client.get_chat_member(target, user_id)
            
            # Extract string status safely (supports both Pyrogram v1 string and Pyrogram v2 Enum)
            status_val = str(getattr(member.status, "value", member.status)).lower()
            
            if status_val not in JOINED_STATUSES:
                missing.append(ch)
        except UserNotParticipant:
            missing.append(ch)
        except Exception as e:
            err_name = type(e).__name__
            logging.info(f"[ForceSub] Status check for {ch['username']} (User: {user_id}): {err_name} - {e}")
            if "UserNotParticipant" in err_name:
                missing.append(ch)

    if not missing:
        _verified_cache[user_id] = now + CACHE_TTL

    return missing

def build_fsub_markup(missing=None):
    if missing is None:
        missing = FSUB_CHANNELS
    btn_list = []
    for ch in missing:
        btn_list.append([InlineKeyboardButton(f"➕ {ch['name']}", url=ch["url"])])
    btn_list.append([InlineKeyboardButton("🔄 Verify / Try Again", callback_data="check_fsub_join")])
    return InlineKeyboardMarkup(btn_list)

def build_fsub_text(mention="User"):
    return (
        "⚠️ <b>Access Restricted!</b>\n\n"
        f"नमस्ते {mention}!\n"
        "बॉट के किसी भी <b>Command</b> या <b>Button</b> का उपयोग करने के लिए, आपको हमारे दोनों चैनल्स को जॉइन करना अनिवार्य है:\n\n"
        "1️⃣ <b>Main Channel:</b> @nikbotchannel\n"
        "2️⃣ <b>Support Group:</b> @niksupportgroup\n\n"
        "👇 नीचे दिए गए बटनों से दोनों जॉइन करें, फिर <b>Verify</b> दबाएं:"
    )

# Group -1 runs BEFORE all normal message handlers (group 0)
@app.on_message(filters.private, group=-1)
async def forcesub_message_handler(client, message: Message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    if is_admin(user_id):
        return

    # If user is in an active ask() prompt, don't interrupt regular text inputs (e.g. OTP/phone)
    listening_chats = getattr(client, "listening", {})
    if (message.chat.id in listening_chats or user_id in listening_chats) and not (message.text and message.text.startswith("/")):
        return

    missing = await get_missing_channels(client, user_id)
    if missing:
        try:
            await message.reply_text(
                build_fsub_text(message.from_user.mention),
                reply_markup=build_fsub_markup(missing),
                disable_web_page_preview=True
            )
        except Exception as e:
            logging.error(f"[ForceSub] Send message error: {e}")
        message.stop_propagation()

# Group -1 runs BEFORE all normal callback query handlers (group 0)
@app.on_callback_query(group=-1)
async def forcesub_callback_handler(client, query: CallbackQuery):
    if not query.from_user:
        return
    user_id = query.from_user.id

    # If the user clicked the verification button
    if query.data == "check_fsub_join":
        _verified_cache.pop(user_id, None)  # Invalidate cache for fresh check
        missing = await get_missing_channels(client, user_id)
        if not missing:
            await query.answer("✅ बहुत बढ़िया! आपने दोनों चैनल्स जॉइन कर लिए हैं।", show_alert=True)
            try:
                from Extractor.modules.start import buttons, photo
                from Extractor.core import script
                caption = script.START_TXT.format(query.from_user.mention)
                try:
                    await query.message.delete()
                except Exception:
                    pass
                await client.send_photo(
                    chat_id=query.message.chat.id,
                    photo=photo(),
                    caption=caption,
                    reply_markup=buttons
                )
            except Exception:
                try:
                    await query.edit_message_text(
                        "✅ <b>सफलतापूर्वक सत्यापित!</b>\n\nआप हमारे दोनों चैनल्स से जुड़ चुके हैं। अब बॉट का उपयोग करने के लिए /start भेजें।"
                    )
                except Exception:
                    pass
        else:
            await query.answer("❌ आपने अभी तक दोनों चैनल जॉइन नहीं किए हैं!\nकृपया दोनों जॉइन करने के बाद ही Verify दबाएं।", show_alert=True)
            try:
                await query.edit_message_reply_markup(reply_markup=build_fsub_markup(missing))
            except Exception:
                pass
        query.stop_propagation()
        return

    if is_admin(user_id):
        return

    # For any other button click across the entire bot
    missing = await get_missing_channels(client, user_id)
    if missing:
        await query.answer("⚠️ कृपया पहले हमारे दोनों चैनल्स को जॉइन करें!", show_alert=True)
        try:
            await query.message.reply_text(
                build_fsub_text(query.from_user.mention),
                reply_markup=build_fsub_markup(missing),
                disable_web_page_preview=True
            )
        except Exception:
            pass
        query.stop_propagation()
