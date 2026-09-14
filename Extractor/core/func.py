import re
import asyncio
from datetime import datetime
from pyrogram.errors import UserNotParticipant
from pyrogram.types import *
from config import CHANNEL_ID2
from Extractor.core import script
from Extractor.core.mongo.plans_db import premium_users


async def chk_user(query, user_id):
    user = await premium_users()
    if user_id in user:
        await query.answer("Premium User!!")
        return 0
    else:
        await query.answer("Sir, you don't have premium access!!", show_alert=True)
        return 1


async def get_seconds(time_string):
    def extract_value_and_unit(ts):
        value = ""
        unit = ""

        index = 0
        while index < len(ts) and ts[index].isdigit():
            value += ts[index]
            index += 1

        unit = ts[index:].lstrip()

        if value:
            value = int(value)

        return value, unit

    value, unit = extract_value_and_unit(time_string.lower())

    if unit in ['s', 'sec', 'secs', 'second', 'seconds']:
        return value
    elif unit in ['m', 'min', 'mins', 'minute', 'minutes']:
        return value * 60
    elif unit in ['h', 'hr', 'hrs', 'hour', 'hours']:
        return value * 3600
    elif unit in ['d', 'day', 'days']:
        return value * 86400
    elif unit in ['month', 'months', 'mo']:
        return value * 86400 * 30
    elif unit in ['y', 'yr', 'yrs', 'year', 'years']:
        return value * 86400 * 365
    else:
        return 0


async def subscribe(app, message):
    try:
        if not message.from_user:
            return 0
        user_id = message.from_user.id
        from Extractor.modules.forcesub import get_missing_channels, build_fsub_text, build_fsub_markup
        missing = await get_missing_channels(app, user_id)
        if missing:
            await message.reply_text(
                build_fsub_text(message.from_user.mention),
                reply_markup=build_fsub_markup(missing),
                disable_web_page_preview=True
            )
            return 1
        return 0
    except Exception as e:
        print(f"Subscribe error: {e}")
        return 0
