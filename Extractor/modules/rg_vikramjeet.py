from pyrogram import Client, filters
from pyrogram.types import Message
from Extractor.modules.appex_v4 import appex_v5_txt
from Extractor import app

@app.on_message(filters.command(["rgvikramjeet"]))
async def rgvikramjeet(client: Client, m: Message):
    api = "rgvikramjeetapi.classx.co.in"
    name = "RG Vikramjeet"
    await appex_v5_txt(app, m, api, name)
