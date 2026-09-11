import asyncio
import importlib
import os
import threading
import logging
from pyrogram import idle
from Extractor.modules import ALL_MODULES

# Auto-start web server in background thread for Render Web Service port detection
def _start_keep_alive():
    try:
        from app import app as flask_app
        # Silence werkzeug access logs
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.ERROR)
        port = int(os.environ.get("PORT", 8080))
        flask_app.run(host="0.0.0.0", port=port, use_reloader=False)
    except Exception as e:
        print(f"Keep-alive web server notice: {e}")

# Always start keep-alive server so Render / cloud host detects open port immediately
threading.Thread(target=_start_keep_alive, daemon=True).start()

try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

async def sumit_boot():
    for all_module in ALL_MODULES:
        importlib.import_module("Extractor.modules." + all_module)

    print("» ʙᴏᴛ ᴅᴇᴘʟᴏʏ sᴜᴄᴄᴇssғᴜʟʟʏ ✨ 🎉")
    
    # Keep bot alive continuously
    while True:
        try:
            await idle()
            await asyncio.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            print("» Bot shutdown requested.")
            break
        except Exception as e:
            print(f"» Idle event error: {e}, keeping bot active...")
            await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        loop.run_until_complete(sumit_boot())
    except KeyboardInterrupt:
        print("Bot process interrupted by user.")
    finally:
        # Cancel pending tasks to avoid "destroyed but pending" error
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()
