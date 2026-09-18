import os
from os import getenv


# ------------------------------------------------
API_ID = int(os.environ.get("API_ID", "11099708"))
# ------------------------------------------------
API_HASH = os.environ.get("API_HASH","3b8ddf3f92d4b9f897777d4fe2a245e2")
# ------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8797094599:AAHTtQIZ3eGPmsoVLiCIVODTKS7GVFKS7zw")
# ------------------------------------------------
BOT_USERNAME = os.environ.get("BOT_USERNAME", "@txtnikbot")
BOT_TEXT = "ąŋơŋơɱųʂცཞơ"
# ------------------------------------------------
OWNER_ID = int(os.environ.get("OWNER_ID", "8693484744"))
ADMINS = [int(x) for x in os.environ.get("ADMINS", "").split(",") if x.strip().isdigit()]
if OWNER_ID not in ADMINS:
    ADMINS.append(OWNER_ID)
# ------------------------------------------------
# //LOG CHANNEL ID 
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003716177168"))

# //FORCE_CHANNEL_ID
CHANNEL_ID2 = int(os.environ.get("CHANNEL_ID2", "0")) 
FSUB_CHANNELS = [
    {"name": "📢 Main Channel", "username": "nikbotchannel", "url": "https://t.me/nikbotchannel"},
    {"name": "💬 Support Group", "username": "niksupportgroup", "url": "https://t.me/niksupportgroup"}
]
# ------------------------------------------------
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://sofisnyder536_db_user:qADieTbcEahcRj39@cluster0.7wyviws.mongodb.net")
# -----------------------------------------------
PREMIUM_LOGS = int(os.environ.get("PREMIUM_LOGS", "-1003716177168"))
# -----------------------------------------------
join = '<a href="https://t.me/nikbotchannel">✳️ JOIN BACKUP</a>'
# -----------------------------------------------
UNSPLASH_ACCESS_KEY = 'RabDRmuXXBobanmwwbvpP5LwoG4J8ox34y5Sstz-9jk'
# -----------------------------------------------
UNSPLASH_QUERY = 'animal baby'
# -----------------------------------------------
ADMIN_BOT_USERNAME = "ananomusbro" #without @

THUMB_URL = os.environ.get("THUMB_URL", "https://i.postimg.cc/cJSKmfNZ/ahmed-zayan-f-Syq-R8z3r-N8-unsplash.jpg")
TXT_LOGO_URL = os.environ.get("TXT_LOGO_URL", "https://i.postimg.cc/SQ2MmSd5/ahmed-zayan-wx6ax-Nws-Tb-Y-unsplash.jpg")
LOGO_URL = TXT_LOGO_URL

