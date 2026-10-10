import asyncio

# --- EVENT LOOP FIX (इसे सबसे ऊपर ही रखना है) ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
# ------------------------------------------------

import logging
import os
from pyromod import listen
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

# Create sessions directory if it doesn't exist
if not os.path.exists("sessions"):
    os.makedirs("sessions")

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s",
    level=logging.INFO,
)

app = Client(
    "Extractor",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir="sessions",
    workers=200,
)

# Initialize pyromod attributes
app.listening = {}
app.listening_cb = {}
app.waiting_input = {}

async def info_bot():
    global BOT_ID, BOT_NAME, BOT_USERNAME
    try:
        await app.start()
    except Exception as e:
        err_str = str(e)
        if "ACCESS_TOKEN_EXPIRED" in err_str or "AccessTokenExpired" in type(e).__name__:
            # Remove stale session file
            if os.path.exists("sessions"):
                for sf in os.listdir("sessions"):
                    if sf.endswith(".session") or sf.endswith(".session-journal"):
                        try:
                            os.remove(os.path.join("sessions", sf))
                            logging.warning(f"Removed stale session file: {sf}")
                        except Exception:
                            pass
            logging.error(
                "\n" + "="*60 + "\n"
                "❌ [CRITICAL ERROR] BOT_TOKEN EXPIRED / INVALID!\n"
                "Telegram says: [400 ACCESS_TOKEN_EXPIRED]\n\n"
                "समाधान (How to fix on Render):\n"
                "1. Telegram पर @BotFather खोलें और नया टोकन लें (/token या /newbot)।\n"
                "2. Render Dashboard -> Environment Variables में जाएं।\n"
                "3. 'BOT_TOKEN' को नए टोकन से अपडेट करें।\n"
                "4. Render पर 'Deploy' -> 'Clear build cache & deploy' करें।\n"
                + "="*60 + "\n"
            )
            raise SystemExit(1)
        raise e

    getme = await app.get_me()
    BOT_ID = getme.id
    BOT_USERNAME = getme.username
    if getme.last_name:
        BOT_NAME = getme.first_name + " " + getme.last_name
    else:
        BOT_NAME = getme.first_name

    # Pre-resolve log channel so Pyrogram caches peer access_hash
    try:
        from config import CHANNEL_ID, PREMIUM_LOGS, FSUB_CHANNELS
        for ch in [CHANNEL_ID, PREMIUM_LOGS]:
            if ch and ch != 0:
                try:
                    await app.get_chat(ch)
                    logging.info(f"Log channel resolved: {ch}")
                    break
                except Exception as e:
                    logging.debug(f"Could not resolve log channel {ch}: {e}")

        # Pre-resolve ForceSub channels
        for ch in FSUB_CHANNELS:
            try:
                target = f"@{ch['username'].lstrip('@')}"
                fsub_chat = await app.get_chat(target)
                logging.info(f"ForceSub channel pre-resolved: {target} -> {fsub_chat.id}")
            except Exception as e:
                logging.warning(f"Could not pre-resolve ForceSub channel {ch.get('username')}: {e}")
    except Exception as e:
        logging.warning(f"Error during channel resolution: {e}")

# अब यहाँ नीचे loop बिना किसी एरर के काम करेगा
loop.run_until_complete(info_bot())
