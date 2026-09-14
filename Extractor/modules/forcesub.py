import time
import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.errors import UserNotParticipant
from Extractor import app
from config import ADMINS, OWNER_ID, FSUB_CHANNELS

# Cache to store verified users: {user_id: expire_timestamp}
# This prevents flooding Telegram API on every single button press or message
_verified_cache = {}
CACHE_TTL = 90  # 90 seconds cache

def is_admin(user_id: int) -> bool:
    if not user_id:
        return False
    return user_id == OWNER_ID or user_id in ADMINS

async def get_missing_channels(client, user_id: int):
    if is_admin(user_id):
        return []

    now = time.time()
    if user_id in _verified_cache and _verified_cache[user_id] > now:
        return []

    missing = []
    for ch in FSUB_CHANNELS:
        try:
            member = await client.get_chat_member(ch["username"], user_id)
            if member.status in ["kicked", "banned"]:
                missing.append(ch)
            elif member.status not in ["creator", "administrator", "member", "restricted"]:
                missing.append(ch)
        except UserNotParticipant:
            missing.append(ch)
        except Exception as e:
            # If temporary network issue or peer resolution error, log without falsely blocking
            print(f"[ForceSub] Notice checking {ch['username']} for {user_id}: {e}")

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

    # If user is in an active ask() prompt, don't interrupt non-command input
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
            print(f"[ForceSub] Send message error: {e}")
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
