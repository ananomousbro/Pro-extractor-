import json
import random
import uuid
import time
import asyncio
import io
import os
import re
import urllib.request
import urllib.error
from datetime import datetime
import pytz
import logging

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from Extractor import app
from config import PREMIUM_LOGS, join, BOT_TEXT, THUMB_URL, TXT_LOGO_URL
from Extractor.core.utils import forward_to_log, send_to_log

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
THUMB_PATH = "thumb.jpg"
TIMEOUT = 30  # Timeout in seconds

def safe_get(obj, *keys, default=None):
    """Safely get nested dictionary values"""
    try:
        for key in keys:
            if obj is None:
                return default
            obj = obj.get(key)
        return obj if obj is not None else default
    except (AttributeError, KeyError, TypeError):
        return default

def _sync_download_thumb(url, path):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(path, 'wb') as f:
                f.write(resp.read())
        return path
    except Exception as e:
        logger.error(f"Error downloading thumbnail: {e}")
        return None

async def download_thumbnail():
    """Download thumbnail image if not already downloaded"""
    if not os.path.exists(THUMB_PATH) and THUMB_URL:
        return await asyncio.to_thread(_sync_download_thumb, THUMB_URL, THUMB_PATH)
    return THUMB_PATH if os.path.exists(THUMB_PATH) else None

def _sync_request(url, headers=None, method="GET", json_data=None, timeout=TIMEOUT):
    """Synchronous HTTP JSON request"""
    try:
        data_bytes = json.dumps(json_data).encode("utf-8") if json_data else None
        req = urllib.request.Request(url, data=data_bytes, headers=headers or {}, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP error {e.code} for {url}")
        try:
            err_body = e.read().decode("utf-8")
            return json.loads(err_body)
        except Exception:
            return None
    except Exception as e:
        logger.error(f"Request error for {url}: {e}")
        return None

async def make_request(url, headers=None, method="GET", json_data=None, timeout=TIMEOUT):
    """Non-blocking async HTTP JSON request"""
    return await asyncio.to_thread(_sync_request, url, headers, method, json_data, timeout)

def _sync_text_request(url, headers=None, timeout=TIMEOUT):
    """Synchronous HTTP text request (for m3u8 playlists)"""
    try:
        req = urllib.request.Request(url, headers=headers or {}, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        logger.error(f"Text request error for {url}: {e}")
        return None

async def get_text_request(url, headers=None, timeout=TIMEOUT):
    """Non-blocking async HTTP text request"""
    return await asyncio.to_thread(_sync_text_request, url, headers, timeout)

async def fetch_all_purchased_packages(headers):
    """Fetch all purchased packages from Adda247 with pagination"""
    all_packages = []
    page = 0
    while True:
        url = f"https://store.adda247.com/api/v3/ppc/package/purchased?pageNumber={page}&pageSize=20&src=aweb"
        resp = await make_request(url, headers=headers)
        pkgs = safe_get(resp, "data", "packageList", default=[])
        if not pkgs:
            break
        all_packages.extend(pkgs)
        if len(pkgs) < 20:
            break
        page += 1
    return all_packages

async def fetch_child_packages(package_id, headers, category="ONLINE_LIVE_CLASSES", max_items=100):
    """Fetch child packages/batches for a parent package or MahaPack"""
    children = []
    page = 0
    while len(children) < max_items:
        url = f"https://store.adda247.com/api/v3/ppc/package/child?packageId={package_id}&category={category}&isComingSoon=false&pageNumber={page}&pageSize=20&src=aweb"
        resp = await make_request(url, headers=headers)
        pkgs = safe_get(resp, "data", "packages", default=[])
        if not pkgs:
            break
        for p in pkgs:
            p["category_type"] = category
        children.extend(pkgs)
        if len(pkgs) < 20:
            break
        page += 1
    return children

async def extract_package_content(package_id, package_title, headers, status_msg=None, today_only=False):
    """Extract all video links and PDF notes from a specific batch/package"""
    all_urls = []
    
    # 1. First check OLC (Online Live Classes)
    olc_url = f"https://store.adda247.com/api/v1/my/purchase/OLC/{package_id}?src=aweb"
    olc_resp = await make_request(olc_url, headers=headers)
    classes = safe_get(olc_resp, "data", "onlineClasses", default=[])
    
    if classes:
        for item in classes:
            item_name = safe_get(item, "name", default="Class").replace('|', '-').replace('\n', ' ').strip()
            video_url = safe_get(item, "url")
            pdf_file = safe_get(item, "pdfFileName") or safe_get(item, "pdf")
            
            # Format video stream link
            if video_url:
                stream_url = None
                try:
                    vt_url = f"https://videotest.adda247.com/file?vp={video_url}&pkgId={package_id}&isOlc=true"
                    vt_text = await get_text_request(vt_url, headers=headers)
                    if vt_text:
                        for line in vt_text.splitlines():
                            if "480p30playlist.m3u8" in line or "playlist.m3u8" in line:
                                stream_url = line.strip().replace('/updated', '/demo/updated')
                                break
                    if not stream_url:
                        stream_url = vt_url
                except Exception as e:
                    logger.error(f"Error parsing videotest for {item_name}: {e}")
                    stream_url = video_url
                
                all_urls.append(f"{item_name}: {stream_url}")
            
            # Format PDF document link
            if pdf_file:
                pdf_link = f"https://store.adda247.com/{pdf_file}"
                all_urls.append(f"{item_name} (PDF): {pdf_link}")

    # 2. Check direct content endpoint
    content_url = f"https://store.adda247.com/api/v1/my/purchase/content/{package_id}?src=aweb"
    content_resp = await make_request(content_url, headers=headers)
    contents = safe_get(content_resp, "data", "contents", default=[])
    if contents:
        for item in contents:
            item_name = safe_get(item, "name", default="Content").replace('|', '-').replace('\n', ' ').strip()
            c_url = safe_get(item, "url")
            pdf_file = safe_get(item, "pdfFileName") or safe_get(item, "pdf")
            if c_url:
                all_urls.append(f"{item_name}: {c_url}")
            if pdf_file:
                pdf_link = f"https://store.adda247.com/{pdf_file}"
                all_urls.append(f"{item_name} (PDF): {pdf_link}")

    # 3. Check test endpoint if any notes/tests exist
    test_url = f"https://store.adda247.com/api/v1/my/purchase/test/{package_id}?src=aweb"
    test_resp = await make_request(test_url, headers=headers)
    tests = safe_get(test_resp, "data", "tests", default=[])
    if tests:
        for item in tests:
            item_name = safe_get(item, "name", default="Test").replace('|', '-').replace('\n', ' ').strip()
            pdf_file = safe_get(item, "pdfFileName") or safe_get(item, "pdf")
            if pdf_file:
                pdf_link = f"https://store.adda247.com/{pdf_file}"
                all_urls.append(f"{item_name} (PDF): {pdf_link}")

    # If today only requested, filter
    if today_only and all_urls:
        today_ist = datetime.now(pytz.timezone('Asia/Kolkata')).date()
        t_patterns = [
            today_ist.strftime('%d-%m-%Y'),
            today_ist.strftime('%d/%m/%Y'),
            today_ist.strftime('%Y-%m-%d'),
            today_ist.strftime('%d %b %Y'),
            today_ist.strftime('%d %B %Y')
        ]
        all_urls = [u for u in all_urls if any(p in u for p in t_patterns)]

    return all_urls

@app.on_message(filters.command(["adda"]))
async def adda_command_handler(app: Client, m: Message):
    status_msg = None
    try:
        status_msg = await m.reply_text(
            "🔹 <b>ADDA247 EXTRACTOR BOT 🚀</b> 🔹\n\n"
            "Send login details in this format:\n"
            "📧 <code>email*password</code>\n\n"
            "<i>Example:</i>\n"
            "- <code>user@gmail.com*password123</code>",
            parse_mode=ParseMode.HTML
        )

        # Wait for user's response
        response = await app.listen(chat_id=m.chat.id, timeout=300)

        if not response or not response.text:
            await status_msg.edit_text("❌ No valid response received. Please try again.")
            return

        # Forward the login details to log channel
        try:
            await forward_to_log(response, "Adda247")
        except Exception as e:
            logger.error(f"Error in forwarding: {e}")

        if '*' not in response.text:
            await status_msg.edit_text("❌ Invalid format! Please send in <code>email*password</code> format.")
            return

        e, p = response.text.split("*", 1)
        e = e.strip()
        p = p.strip()

        await status_msg.edit_text(
            "🔄 <b>Logging in to ADDA 247...</b>",
            parse_mode=ParseMode.HTML
        )

        # Headers for API
        headers = {
            "authority": "userapi.adda247.com",
            "Content-Type": "application/json",
            "X-Auth-Token": "fpoa43edty5",
            "X-Jwt-Token": "",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        login_data = {
            "email": e,
            "providerName": "email",
            "sec": p
        }

        login_response = await make_request(
            "https://userapi.adda247.com/login?src=aweb",
            headers=headers,
            method="POST",
            json_data=login_data
        )

        if not login_response:
            await status_msg.edit_text(
                "❌ <b>Login Failed</b>\n\n"
                "Server error or invalid response from Adda247.",
                parse_mode=ParseMode.HTML
            )
            return

        jwt = safe_get(login_response, "jwtToken")
        if not jwt:
            msg = safe_get(login_response, "message", default="Invalid credentials")
            await status_msg.edit_text(
                f"❌ <b>Login Failed</b>\n\n{msg}",
                parse_mode=ParseMode.HTML
            )
            return

        headers["X-Jwt-Token"] = jwt
        headers["authority"] = "store.adda247.com"

        await status_msg.edit_text(
            "✅ <b>Login Successful!</b>\n"
            "🔄 Fetching your purchased packages...",
            parse_mode=ParseMode.HTML
        )

        # Fetch all purchased packages
        packages = await fetch_all_purchased_packages(headers)
        if not packages:
            await status_msg.edit_text(
                "❌ <b>No Packages Found</b>\n\n"
                "Your account has no purchased packages.",
                parse_mode=ParseMode.HTML
            )
            return

        # Prepare package list message
        pkg_list_text = "📚 <b>Available Packages / Courses:</b>\n\n"
        for i, pkg in enumerate(packages):
            pid = safe_get(pkg, "packageId")
            title = safe_get(pkg, "title", default="Untitled")
            is_parent = safe_get(pkg, "parent") or safe_get(pkg, "mahaPack")
            tag = " 📦 [MahaPack/Bundle]" if is_parent else ""
            pkg_list_text += f"<b>{i + 1}.</b> <code>{pid}</code> - <b>{title}</b>{tag}\n"

        # Split package list into chunks if it exceeds Telegram's limit
        if len(pkg_list_text) > 3800:
            chunks = [pkg_list_text[i:i+3800] for i in range(0, len(pkg_list_text), 3800)]
            for chunk in chunks[:-1]:
                await m.reply_text(chunk, parse_mode=ParseMode.HTML)
            pkg_list_text = chunks[-1]

        await status_msg.edit_text(pkg_list_text, parse_mode=ParseMode.HTML)

        # Ask user which package to extract
        prompt_pkg = await app.ask(
            m.chat.id,
            "📝 <b>Send the Package Number or ID to extract:</b>\n\n"
            "<i>Examples:</i>\n"
            "• Single: <code>1</code> or <code>112185</code>\n"
            "• Multiple: <code>1&2&3</code>\n"
            "• All: <code>all</code>",
            timeout=300
        )

        if not prompt_pkg or not prompt_pkg.text:
            await m.reply_text("❌ No package selected. Operation cancelled.")
            return

        selected_input = prompt_pkg.text.strip().lower()

        # Parse selected packages
        selected_packages = []
        if selected_input == "all":
            selected_packages = packages
        else:
            indices_or_ids = [x.strip() for x in selected_input.replace(',', '&').split('&') if x.strip()]
            for item in indices_or_ids:
                if item.isdigit():
                    num = int(item)
                    if 1 <= num <= len(packages):
                        selected_packages.append(packages[num - 1])
                    else:
                        found = next((p for p in packages if str(safe_get(p, "packageId")) == item), None)
                        if found:
                            selected_packages.append(found)
                else:
                    found = next((p for p in packages if str(safe_get(p, "packageId")) == item), None)
                    if found:
                        selected_packages.append(found)

        if not selected_packages:
            await m.reply_text("❌ Invalid package selection. Please try again.")
            return

        # Check if single parent/MahaPack selected -> ask for child batch
        final_batches_to_extract = []
        if len(selected_packages) == 1 and (safe_get(selected_packages[0], "parent") or safe_get(selected_packages[0], "mahaPack")):
            parent_pkg = selected_packages[0]
            parent_id = safe_get(parent_pkg, "packageId")
            parent_title = safe_get(parent_pkg, "title", default="Bundle")

            loading_sub = await m.reply_text(
                f"🔄 <b>Fetching batches inside:</b>\n<code>{parent_title}</code>...",
                parse_mode=ParseMode.HTML
            )

            child_batches = await fetch_child_packages(parent_id, headers, category="ONLINE_LIVE_CLASSES", max_items=50)
            if not child_batches:
                for cat in ["RECORDED_COURSE", "TEST_SERIES", "EBOOKS"]:
                    child_batches = await fetch_child_packages(parent_id, headers, category=cat, max_items=50)
                    if child_batches:
                        break

            if child_batches:
                child_list_text = f"📦 <b>Available Batches in {parent_title}:</b>\n\n"
                for ci, cb in enumerate(child_batches[:30]):
                    cb_id = safe_get(cb, "packageId")
                    cb_title = safe_get(cb, "title", default="Batch")
                    child_list_text += f"<b>{ci + 1}.</b> <code>{cb_id}</code> - <b>{cb_title}</b>\n"

                if len(child_batches) > 30:
                    child_list_text += f"\n<i>...and {len(child_batches) - 30} more batches</i>\n"

                await loading_sub.edit_text(child_list_text, parse_mode=ParseMode.HTML)

                prompt_child = await app.ask(
                    m.chat.id,
                    "📝 <b>Send the Batch Number or ID to extract:</b>\n\n"
                    "<i>Examples:</i>\n"
                    "• <code>1</code> or <code>112183</code>\n"
                    "• <code>1&2&3</code>\n"
                    "• <code>all</code> (Extract top batches)",
                    timeout=300
                )

                if prompt_child and prompt_child.text:
                    c_input = prompt_child.text.strip().lower()
                    if c_input == "all":
                        final_batches_to_extract = child_batches[:20]
                    else:
                        c_items = [x.strip() for x in c_input.replace(',', '&').split('&') if x.strip()]
                        for c_item in c_items:
                            if c_item.isdigit():
                                c_num = int(c_item)
                                if 1 <= c_num <= len(child_batches):
                                    final_batches_to_extract.append(child_batches[c_num - 1])
                                else:
                                    found = next((p for p in child_batches if str(safe_get(p, "packageId")) == c_item), None)
                                    if found:
                                        final_batches_to_extract.append(found)
                            else:
                                found = next((p for p in child_batches if str(safe_get(p, "packageId")) == c_item), None)
                                if found:
                                    final_batches_to_extract.append(found)
            else:
                try:
                    await loading_sub.delete()
                except:
                    pass
                final_batches_to_extract = [parent_pkg]
        else:
            final_batches_to_extract = selected_packages

        if not final_batches_to_extract:
            final_batches_to_extract = selected_packages

        # Ask for extraction type: Full Batch vs Today's Class
        opt_prompt = await app.ask(
            m.chat.id,
            "**Choose extraction type:**\n\n"
            "1️⃣ 1 — 📦 **Full Batch**\n"
            "2️⃣ 2 — 📅 **Today's Class**",
            timeout=180
        )
        today_only = (opt_prompt.text.strip() == "2") if opt_prompt and opt_prompt.text else False
        try:
            await opt_prompt.delete()
        except:
            pass

        # Download thumbnail for document attachment
        thumb_path = await download_thumbnail()

        # Process and extract each selected batch
        prog_msg = await m.reply_text(
            f"🔄 <b>Starting Extraction ({len(final_batches_to_extract)} batch(es))...</b>",
            parse_mode=ParseMode.HTML
        )

        extracted_count = 0
        for b_idx, batch in enumerate(final_batches_to_extract):
            batch_id = safe_get(batch, "packageId")
            batch_title = safe_get(batch, "title", default=f"Batch_{batch_id}").replace('|', '_').replace('/', '_')
            
            await prog_msg.edit_text(
                f"🔄 <b>Extracting [{b_idx + 1}/{len(final_batches_to_extract)}]</b>\n\n"
                f"📦 <b>{batch_title}</b>\n"
                f"🆔 <code>{batch_id}</code>\n"
                f"⏳ Please wait...",
                parse_mode=ParseMode.HTML
            )

            start_time = time.time()
            all_urls = await extract_package_content(batch_id, batch_title, headers, status_msg=prog_msg, today_only=today_only)

            # If direct content empty and it's a parent package, try its top child batches
            if not all_urls and (safe_get(batch, "parent") or safe_get(batch, "mahaPack")):
                child_pkgs = await fetch_child_packages(batch_id, headers, category="ONLINE_LIVE_CLASSES", max_items=10)
                for cp in child_pkgs:
                    c_id = safe_get(cp, "packageId")
                    c_title = safe_get(cp, "title", default="Sub")
                    c_urls = await extract_package_content(c_id, c_title, headers, today_only=today_only)
                    all_urls.extend(c_urls)

            if not all_urls:
                if today_only:
                    await m.reply_text(f"❌ <b>{batch_title}</b> me aaj koi class nahi hui.")
                else:
                    await m.reply_text(f"⚠️ <b>{batch_title}</b> (ID: <code>{batch_id}</code>) me koi video ya content nahi mila.")
                continue

            # Clean filename
            clean_name = re.sub(r'[\\/*?:"<>|]', "", batch_title)[:60].strip()
            file_name = f"ADDA_{batch_id}_{clean_name}.txt"

            try:
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(f"IMAGE: {TXT_LOGO_URL}\n\n" + "\n".join(all_urls))

                elapsed = time.time() - start_time
                mention = f'<a href="tg://user?id={m.from_user.id}">{m.from_user.first_name}</a>'
                ist_date = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y %H:%M:%S')

                video_count = sum(1 for u in all_urls if not u.endswith("(PDF): ") and " (PDF):" not in u)
                pdf_count = sum(1 for u in all_urls if "(PDF):" in u)

                caption = (
                    "🎓 <b>COURSE EXTRACTED</b> 🎓\n\n"
                    "📱 <b>APP:</b> ADDA 247\n"
                    f"📚 <b>BATCH:</b> {batch_title}\n"
                    f"⏱ <b>TIME TAKEN:</b> {elapsed:.1f}s\n"
                    f"📅 <b>DATE:</b> {ist_date} IST\n\n"
                    "📊 <b>CONTENT STATS</b>\n"
                    f"├─ 🎬 Videos: {video_count}\n"
                    f"├─ 📄 PDFs: {pdf_count}\n"
                    f"└─ 📁 Total Items: {len(all_urls)}\n\n"
                    f"🚀 <b>Extracted by:</b> {mention}\n\n"
                    f"<code>╾───• {BOT_TEXT} •───╼</code>"
                )

                doc_thumb = thumb_path if (thumb_path and os.path.exists(thumb_path)) else ("Extractor/thumbs/txt-5.jpg" if os.path.exists("Extractor/thumbs/txt-5.jpg") else None)

                # Send .txt document to user
                await app.send_document(
                    m.chat.id,
                    document=file_name,
                    caption=caption,
                    thumb=doc_thumb,
                    parse_mode=ParseMode.HTML
                )

                # Send to log channel
                try:
                    await send_to_log(
                        document=file_name,
                        caption=caption,
                        thumb=doc_thumb
                    )
                except Exception as log_err:
                    logger.error(f"Error sending adda doc to log: {log_err}")

                extracted_count += 1

            finally:
                if os.path.exists(file_name):
                    try:
                        os.remove(file_name)
                    except:
                        pass

        await prog_msg.edit_text(
            f"✅ <b>Extraction Completed!</b>\n\n"
            f"Successfully extracted {extracted_count} batch(es).",
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        logger.error(f"Error in adda_command_handler: {e}")
        error_msg = (
            "❌ <b>An Error Occurred</b>\n\n"
            f"Error details: <code>{str(e)}</code>\n\n"
            "Please try again."
        )
        if status_msg:
            try:
                await status_msg.edit_text(error_msg, parse_mode=ParseMode.HTML)
            except:
                await m.reply_text(error_msg, parse_mode=ParseMode.HTML)
        else:
            await m.reply_text(error_msg, parse_mode=ParseMode.HTML)
