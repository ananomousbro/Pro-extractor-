import re
import asyncio
ListenerTimeout = asyncio.TimeoutError
import requests, os, sys, re
import json, asyncio
import subprocess
import datetime
import time
import logging
from typing import List, Dict, Tuple, Any
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from Extractor import app
from config import  PREMIUM_LOGS,BOT_TEXT
from pyrogram import Client, filters, idle
from pyrogram.types import Message
import asyncio
ListenerTimeout = asyncio.TimeoutError
from subprocess import getstatusoutput
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import config
from Extractor.core.utils import forward_to_log, send_to_log
from datetime import datetime
import pytz
# from Extractor.modules.enc import process_file_content  # Add encryption import


join = config.join
india_timezone = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(india_timezone)
time_new = current_time.strftime("%d-%m-%Y %I:%M %p")
THREADPOOL = ThreadPoolExecutor(max_workers=5000)


# Pure Python AES-128-CBC Decryption Engine
_Sbox = [
    0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
    0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0,
    0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15,
    0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75,
    0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84,
    0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF,
    0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8,
    0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2,
    0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73,
    0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB,
    0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79,
    0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08,
    0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A,
    0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E,
    0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF,
    0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16
]
_InvSbox = [0] * 256
for _i, _x in enumerate(_Sbox): _InvSbox[_x] = _i

_Rcon = [0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36, 0x6C, 0xD8, 0xAB, 0x4D, 0x9A, 0x2F, 0x5E, 0xBC, 0x63, 0xC6, 0x97, 0x35, 0x6A, 0xD4, 0xB3, 0x7D, 0xFA, 0xEF, 0xC5, 0x91, 0x39]

def _sub_word_f(word): return [_Sbox[b] for b in word]
def _rot_word_f(word): return word[1:] + word[:1]
def _key_expansion_128_f(key):
    w = [list(key[i:i+4]) for i in range(0, 16, 4)]
    for i in range(4, 44):
        temp = list(w[i - 1])
        if i % 4 == 0:
            temp = _sub_word_f(_rot_word_f(temp))
            temp[0] ^= _Rcon[i // 4]
        w.append([w[i - 4][j] ^ temp[j] for j in range(4)])
    return w

def _inv_sub_bytes_f(state):
    for r in range(4):
        for c in range(4): state[r][c] = _InvSbox[state[r][c]]

def _inv_shift_rows_f(state):
    state[1] = state[1][-1:] + state[1][:-1]
    state[2] = state[2][-2:] + state[2][:-2]
    state[3] = state[3][-3:] + state[3][:-3]

def _gmul_f(a, b):
    p = 0
    for _ in range(8):
        if b & 1: p ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi: a ^= 0x1B
        b >>= 1
    return p

def _inv_mix_columns_f(state):
    for c in range(4):
        a0, a1, a2, a3 = state[0][c], state[1][c], state[2][c], state[3][c]
        state[0][c] = _gmul_f(0x0e, a0) ^ _gmul_f(0x0b, a1) ^ _gmul_f(0x0d, a2) ^ _gmul_f(0x09, a3)
        state[1][c] = _gmul_f(0x09, a0) ^ _gmul_f(0x0e, a1) ^ _gmul_f(0x0b, a2) ^ _gmul_f(0x0d, a3)
        state[2][c] = _gmul_f(0x0d, a0) ^ _gmul_f(0x09, a1) ^ _gmul_f(0x0e, a2) ^ _gmul_f(0x0b, a3)
        state[3][c] = _gmul_f(0x0b, a0) ^ _gmul_f(0x0d, a1) ^ _gmul_f(0x09, a2) ^ _gmul_f(0x0e, a3)

def _add_round_key_f(state, round_key):
    for r in range(4):
        for c in range(4): state[r][c] ^= round_key[c][r]

def _decrypt_block_128_f(block, round_keys):
    state = [[block[r + 4 * c] for c in range(4)] for r in range(4)]
    _add_round_key_f(state, round_keys[40:44])
    for rnd in range(9, 0, -1):
        _inv_shift_rows_f(state)
        _inv_sub_bytes_f(state)
        _add_round_key_f(state, round_keys[rnd*4 : rnd*4+4])
        _inv_mix_columns_f(state)
    _inv_shift_rows_f(state)
    _inv_sub_bytes_f(state)
    _add_round_key_f(state, round_keys[0:4])
    return bytes([state[r][c] for c in range(4) for r in range(4)])

def _pure_aes_cbc_decrypt_f(ciphertext, key=b"638udh3829162018", iv=b"fedcba9876543210"):
    if len(ciphertext) % 16 != 0: return b""
    round_keys = _key_expansion_128_f(key)
    plaintext = bytearray()
    prev = iv
    for i in range(0, len(ciphertext), 16):
        block = ciphertext[i:i+16]
        dec = _decrypt_block_128_f(block, round_keys)
        pt = bytes([dec[j] ^ prev[j] for j in range(16)])
        plaintext.extend(pt)
        prev = block
    if plaintext:
        pad_len = plaintext[-1]
        if 1 <= pad_len <= 16 and plaintext[-pad_len:] == bytes([pad_len]*pad_len):
            plaintext = plaintext[:-pad_len]
    return bytes(plaintext)

def appx_decrypt(enc):
    if not enc or not isinstance(enc, str):
        return ""
    enc_clean = enc.strip()
    if enc_clean.startswith("http://") or enc_clean.startswith("https://"):
        return enc_clean
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        enc_part = enc_clean.split(':')[0].strip()
        if enc_part:
            enc_bytes = b64decode(enc_part)
            if len(enc_bytes) > 0:
                key = b'638udh3829162018'
                iv = b'fedcba9876543210'
                cipher = AES.new(key, AES.MODE_CBC, iv)
                plaintext = unpad(cipher.decrypt(enc_bytes), AES.block_size)
                res = plaintext.decode('utf-8', errors='ignore').strip()
                if res:
                    return res
    except Exception:
        pass
    try:
        enc_part = enc_clean.split(':')[0].strip()
        if enc_part:
            enc_bytes = b64decode(enc_part)
            dec_bytes = _pure_aes_cbc_decrypt_f(enc_bytes)
            res = dec_bytes.decode('utf-8', errors='ignore').strip()
            if res:
                return res
    except Exception:
        pass
    if "http" in enc_clean:
        match = re.search(r'https?://[^\s]+', enc_clean)
        if match:
            return match.group(0)
    return enc_clean


def extract_media_from_data(Title, data, drm_data=None):
    """Extract all available media links (DRM, HLS, MP4, YouTube, PDF) from Appx video data dict."""
    output = []
    if not data or not isinstance(data, dict):
        return output

    video_url = None
    # 1. DRM link
    if drm_data and isinstance(drm_data, list) and len(drm_data) > 0:
        drm_path = drm_data[0].get("path", "")
        if drm_path:
            dec_path = appx_decrypt(drm_path)
            if dec_path:
                video_url = dec_path

    # 2. Fallback to direct video fields
    if not video_url:
        for field in ["download_link", "download_link2", "file_link", "video_player_url",
                      "video_player_lower_url", "video_url", "hls_url", "recording_hls",
                      "stream_url", "video_path", "link"]:
            val = data.get(field)
            if val and isinstance(val, str) and val.strip():
                dec = appx_decrypt(val)
                if dec and ("http" in dec or ".mpd" in dec or ".m3u8" in dec or ".mp4" in dec):
                    video_url = dec
                    break

    # 3. Encrypted links list
    if not video_url:
        enc_links = data.get("encrypted_links")
        if enc_links and isinstance(enc_links, list):
            for el in enc_links:
                if isinstance(el, dict):
                    p = el.get("path") or el.get("url") or el.get("link")
                    if p:
                        dec = appx_decrypt(p)
                        if dec:
                            video_url = dec
                            break

    # 4. YouTube fallback
    if not video_url:
        if data.get("ytFlag") in [1, "1", True] or data.get("youtube_id"):
            yt_id = data.get("youtube_id") or data.get("video_id") or data.get("id")
            if yt_id:
                video_url = f"https://www.youtube.com/watch?v={yt_id}"

    if video_url:
        output.append(f"{Title}:{video_url}\n")

    # PDFs
    pdf_link = appx_decrypt(data.get("pdf_link", "")) if data.get("pdf_link") else None
    if pdf_link and (pdf_link.endswith(".pdf") or "pdf" in pdf_link.lower() or "http" in pdf_link):
        is_enc = data.get("is_pdf_encrypted", 0)
        if str(is_enc) == "1":
            key = appx_decrypt(data.get("pdf_encryption_key", "")) if data.get("pdf_encryption_key") else None
            if key:
                output.append(f"{Title} PDF:{pdf_link}*{key}\n")
            else:
                output.append(f"{Title} PDF:{pdf_link}\n")
        else:
            output.append(f"{Title} PDF:{pdf_link}\n")

    pdf_link2 = appx_decrypt(data.get("pdf_link2", "")) if data.get("pdf_link2") else None
    if pdf_link2 and (pdf_link2.endswith(".pdf") or "pdf" in pdf_link2.lower() or "http" in pdf_link2):
        is_enc2 = data.get("is_pdf2_encrypted", 0)
        if str(is_enc2) == "1":
            key2 = appx_decrypt(data.get("pdf2_encryption_key", "")) if data.get("pdf2_encryption_key") else None
            if key2:
                output.append(f"{Title} PDF2:{pdf_link2}*{key2}\n")
            else:
                output.append(f"{Title} PDF2:{pdf_link2}\n")
        else:
            output.append(f"{Title} PDF2:{pdf_link2}\n")

    return output


async def fetch_appx_html_to_json(session, url, headers=None, data=None):
    clean_headers = dict(headers or {})
    if "Auth-Key" not in clean_headers and "auth-key" not in clean_headers:
        clean_headers["Auth-Key"] = "appxapi"
    if "Client-Service" not in clean_headers and "client-service" not in clean_headers:
        clean_headers["Client-Service"] = "Appx"
    if "Source" not in clean_headers and "source" not in clean_headers:
        clean_headers["Source"] = "windows"
    if "Device-Id" not in clean_headers and "device-id" not in clean_headers:
        clean_headers["Device-Id"] = "L1HF5A800T4"
    if "Is-Safari" not in clean_headers:
        clean_headers["Is-Safari"] = "0"
    if "User-Agent" not in clean_headers:
        clean_headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) everest_impact/0.0.2 Chrome/108.0.5359.215 Electron/22.3.27 Safari/537.36"

    for attempt in range(4):
        try:
            if data:
                async with session.post(url, headers=clean_headers, data=data) as response:
                    text = await response.text()
                    status = getattr(response, "status", 200)
            else:
                async with session.get(url, headers=clean_headers) as response:
                    text = await response.text()
                    status = getattr(response, "status", 200)

            if status == 429 or "Too Many Requests" in text:
                wait_time = (attempt + 1) * 1.5
                logging.warning(f"Rate limited (429) on: {url} - Retrying in {wait_time}s (attempt {attempt + 1}/4)")
                await asyncio.sleep(wait_time)
                continue

            try:
                return json.loads(text)

            except json.JSONDecodeError:
                match = re.search(r'\{"status":', text, re.DOTALL)
                if match:
                    json_str = text[match.start():]
                    try:
                        open_brace_count = 0
                        close_brace_count = 0
                        json_end = -1

                        for i, char in enumerate(json_str):
                            if char == '{':
                                open_brace_count += 1
                            elif char == '}':
                                close_brace_count += 1

                            if open_brace_count > 0 and open_brace_count == close_brace_count:
                                json_end = i + 1
                                break

                        if json_end != -1:
                            return json.loads(json_str[:json_end])
                        else:
                            logging.error(f"Could not find matching closing brace }} in json string: {json_str[:150]}")
                            return None
                    except json.JSONDecodeError:
                        logging.error(f"Could not parse JSON from the end: {json_str[:150]}")
                        return None
                else:
                    logging.warning(f"Could not find JSON in response: {text[:150]}")
                    return None
        except Exception as e:
            logging.exception(f"An error occurred during the request to {url}: {e}")
            if attempt < 3:
                await asyncio.sleep(1)
                continue
            return None
    return None


async def fetch_appx_video_id_details_v2(session, api, selected_batch_id, video_id, ytFlag, headers, folder_wise_course, user_id):
    try:
        res = await fetch_appx_html_to_json(session, f"{api}/get/fetchVideoDetailsById?course_id={selected_batch_id}&folder_wise_course={folder_wise_course}&ytflag={ytFlag}&video_id={video_id}", headers)

        if res and res.get('data'):
            data = res['data']
            Title = data.get("Title", f"Video_{video_id}")
            
            # Quick check if media is already directly extractable
            initial_media = extract_media_from_data(Title, data, None)
            if initial_media:
                return initial_media
            
            # Only call MPD DRM endpoint if direct link not found
            drm_res = await fetch_appx_html_to_json(session, f"{api}/get/get_mpd_drm_links?videoid={video_id}&folder_wise_course={folder_wise_course}", headers)
            drm_data = drm_res.get('data', []) if drm_res else []
            
            return extract_media_from_data(Title, data, drm_data)
        return []
    except Exception as e:
        logging.error(f"Error in fetch_appx_video_id_details_v2: {e}")
        return []



async def fetch_appx_folder_json(session, api, course_id, parent_id, headers):
    for endpoint in [
        f"{api}/get/folder_contentsv3?course_id={course_id}&parent_id={parent_id}&windowsapp=true&start=-1",
        f"{api}/get/folder_contentsv3?course_id={course_id}&parent_id={parent_id}&windowsapp=true&start=0",
        f"{api}/get/folder_contentsv2?course_id={course_id}&parent_id={parent_id}",
        f"{api}/get/parent_folder_contents?course_id={course_id}&current_folder_id={parent_id}"
    ]:
        try:
            res = await fetch_appx_html_to_json(session, endpoint, headers)
            if res and isinstance(res, dict) and res.get("data"):
                return res
        except Exception:
            continue
    return None

async def fetch_appx_folder_contents_v2(session, api, selected_batch_id, folder_id, headers, folder_wise_course, user_id, visited_folders=None, depth=0):
    if visited_folders is None:
        visited_folders = set()
    
    fid_str = str(folder_id).strip()
    if not fid_str or fid_str in visited_folders or depth > 15:
        return []
    visited_folders.add(fid_str)

    logging.info(f"User ID: {user_id} - Fetching folder contents for folder ID: {folder_id} (depth={depth})")
    try:
        res = await fetch_appx_folder_json(session, api, selected_batch_id, folder_id, headers)
        tasks = []
        output = []
        
        if res and "data" in res:
            data = res["data"]
            for item in data:
                Title = item.get("Title", "")
                video_id = item.get("id")
                ytFlag = item.get("ytFlag", 0)
                material_type = item.get("material_type", "")

                if material_type == "VIDEO":
                    if video_id:
                        tasks.append(
                            fetch_appx_video_id_details_v2(session, api, selected_batch_id, video_id, ytFlag, headers, folder_wise_course, user_id))
                
                elif material_type == "PDF" or material_type == "TEST":
                    pdf_link = appx_decrypt(item.get("pdf_link", "")) if item.get("pdf_link", "") and appx_decrypt(item.get("pdf_link", "")).endswith(".pdf") else None
                        
                    is_pdf_encrypted = item.get("is_pdf_encrypted", 0)
                    if pdf_link:
                        if is_pdf_encrypted == 1 or is_pdf_encrypted == "1":
                            key = appx_decrypt(item.get("pdf_encryption_key", "")) if item.get("pdf_encryption_key") else None
                            if key:
                                output.append(f"{Title} PDF:{pdf_link}*{key}\n")
                            else:
                                output.append(f"{Title} PDF:{pdf_link}\n")
                        else:
                            output.append(f"{Title} PDF:{pdf_link}\n")
                            
                    pdf_link2 = appx_decrypt(item.get("pdf_link2", "")) if item.get("pdf_link2", "") and appx_decrypt(item.get("pdf_link2", "")).endswith(".pdf") else None
                        
                    is_pdf2_encrypted = item.get("is_pdf2_encrypted", 0)
                    if pdf_link2:
                        if is_pdf2_encrypted == 1 or is_pdf2_encrypted == "1":
                            key = appx_decrypt(item.get("pdf2_encryption_key", "")) if item.get("pdf2_encryption_key") else None
                            if key:
                                output.append(f"{Title} PDF2:{pdf_link2}*{key}\n")
                            else:
                                output.append(f"{Title} PDF2:{pdf_link2}\n")
                        else:
                            output.append(f"{Title} PDF2:{pdf_link2}\n")

                elif material_type == "IMAGE":
                    thumbnail = item.get("thumbnail")
                    if thumbnail:
                        output.append(f"{Title} IMAGE:{thumbnail}\n")
                   
                elif material_type == "FOLDER":
                    sub_id = item.get("id")
                    if sub_id and str(sub_id).strip() not in visited_folders:
                        folder_results = await fetch_appx_folder_contents_v2(
                            session, api, selected_batch_id, sub_id, headers, folder_wise_course, user_id, visited_folders, depth + 1
                        )
                        if folder_results:
                            output.extend(folder_results)

        if tasks:
            chunk_size = 5
            for i in range(0, len(tasks), chunk_size):
                chunk = tasks[i:i + chunk_size]
                results = await asyncio.gather(*chunk, return_exceptions=True)
                for r in results:
                    if isinstance(r, list):
                        output.extend(r)
                if i + chunk_size < len(tasks):
                    await asyncio.sleep(0.05)

        return output
    except Exception as e:
        logging.error(f"User ID: {user_id} - Error fetching folder contents for Course_id: {selected_batch_id}, Folder_id: {folder_id}. Error: {e}")
        return []


async def fetch_appx_video_id_details_v3(session, api, selected_batch_id, video_id, ytFlag, headers, user_id):
    try:
        res = await fetch_appx_html_to_json(session, f"{api}/get/fetchVideoDetailsById?course_id={selected_batch_id}&folder_wise_course=0&ytflag={ytFlag}&video_id={video_id}", headers)

        if res and res.get('data'):
            data = res['data']
            Title = data.get("Title", f"Video_{video_id}")
            
            initial_media = extract_media_from_data(Title, data, None)
            if initial_media:
                return initial_media
            
            drm_res = await fetch_appx_html_to_json(session, f"{api}/get/get_mpd_drm_links?folder_wise_course=0&videoid={video_id}", headers)
            drm_data = drm_res.get('data', []) if drm_res else []
            
            return extract_media_from_data(Title, data, drm_data)
        return []
    except Exception as e:
        logging.error(f"Error in fetch_appx_video_id_details_v3: {e}")
        return []



def find_appx_matching_apis(search_api, appxapis_file="appxapis.json"):
    try:
        with open(appxapis_file, 'r', encoding='utf-8') as f:
            api_data = json.load(f)
    except FileNotFoundError:
        logging.error(f"Error: Could not find the file: {appxapis_file}")
        return []
    except json.JSONDecodeError:
        logging.error(f"Error: Invalid JSON format in the file: {appxapis_file}")
        return []

    query_str = " ".join(search_api).lower().strip()
    q_clean = query_str.replace(" ", "")
    terms = [t.strip().lower() for t in search_api if t.strip()]

    exact_matches = []
    all_term_matches = []
    any_term_matches = []
    seen = set()

    for item in api_data:
        name = item.get("name", "")
        api_url = item.get("api", "")
        if not api_url or api_url in seen:
            continue

        name_clean = name.lower().replace(" ", "")
        api_clean = api_url.lower()

        if q_clean and (q_clean in name_clean or q_clean in api_clean):
            exact_matches.append(item)
            seen.add(api_url)
        elif terms and all(t in name_clean or t in api_clean for t in terms):
            all_term_matches.append(item)
            seen.add(api_url)
        elif terms and any(t in name_clean or t in api_clean for t in terms if len(t) > 2 and t not in ["with", "the", "and", "app"]):
            any_term_matches.append(item)
            seen.add(api_url)

    return exact_matches + all_term_matches + any_term_matches


async def process_folder_wise_course_0(session, api, selected_batch_id, headers, user_id, status_msg=None, batch_name=''):
    logging.info(f"User ID: {user_id} - Processing folder-wise course 0")
    res = await fetch_appx_html_to_json(session, f"{api}/get/allsubjectfrmlivecourseclass?courseid={selected_batch_id}&start=-1", headers)
    all_outputs = []
    tasks = []
    if res and "data" in res:
        subjects = res["data"]
        for subject in subjects:
            subjectid = subject.get("subjectid")
            sn = subject.get("subject_name", f"Subject {subjectid}")
            if status_msg:
                try:
                    await status_msg.edit(f"🔄 **Processing Course**\n└─ Current: `{batch_name}`\n📂 **Extracting Subject:** `{sn}`")
                except:
                    pass

            res2 = await fetch_appx_html_to_json(session, f"{api}/get/alltopicfrmlivecourseclass?courseid={selected_batch_id}&subjectid={subjectid}&start=-1", headers)
            if res2 and "data" in res2:
                topics = res2["data"]
                for topic in topics:
                    topicid = topic.get("topicid")

                    res3 = await fetch_appx_html_to_json(session, f"{api}/get/livecourseclassbycoursesubtopconceptapiv3?topicid={topicid}&start=-1&courseid={selected_batch_id}&subjectid={subjectid}", headers)
                    if res3 and "data" in res3:
                        data = res3["data"]
                        for item in data:
                            Title = item.get("Title")
                            video_id = item.get("id")
                            ytFlag = item.get("ytFlag")

                            if item.get("material_type") == "PDF" or item.get("material_type") == "TEST":
                                Title = item.get("Title")
                                
                                pdf_link = appx_decrypt(item.get("pdf_link", "")) if item.get("pdf_link", "") and appx_decrypt(item.get("pdf_link", "")).endswith(".pdf") else None
                                                              
                                is_pdf_encrypted = item.get("is_pdf_encrypted")

                                if pdf_link:
                                    if is_pdf_encrypted == 1 or is_pdf_encrypted == "1":
                                        key = appx_decrypt(item.get("pdf_encryption_key"))
                                        if key:
                                            all_outputs.append(f"{Title}:{pdf_link}*{key}\n")
                                        else:
                                            all_outputs.append(f"{Title}:{pdf_link}\n")
                                    else:
                                        all_outputs.append(f"{Title}:{pdf_link}\n")
                                        
                                pdf_link2 = appx_decrypt(item.get("pdf_link2", "")) if item.get("pdf_link2", "") and appx_decrypt(item.get("pdf_link2", "")).endswith(".pdf") else None
                                    
                                is_pdf2_encrypted = item.get("is_pdf2_encrypted")

                                if pdf_link2:
                                    if is_pdf2_encrypted == 1 or is_pdf2_encrypted == "1":
                                        key = appx_decrypt(item.get("pdf2_encryption_key"))
                                        if key:
                                            all_outputs.append(f"{Title}:{pdf_link2}*{key}\n")
                                        else:
                                            all_outputs.append(f"{Title}:{pdf_link2}\n")
                                    else:
                                        all_outputs.append(f"{Title}:{pdf_link2}\n")

                            elif item.get("material_type") == "IMAGE":
                                thumbnail = item.get("thumbnail")
                                if thumbnail:
                                    all_outputs.append(f"{Title}:{thumbnail}\n")
                                    
                            elif item.get("material_type") == "VIDEO":
                                if selected_batch_id is not None and video_id is not None and ytFlag is not None:
                                    tasks.append(
                                        fetch_appx_video_id_details_v3(session, api, selected_batch_id, video_id, ytFlag, headers, user_id))
                                else:
                                    logging.warning(
                                        f"User ID: {user_id} - Skipping video due to None value: course_id={selected_batch_id}, video_id={video_id}, ytflag={ytFlag}")
                    else:
                        logging.warning(f"User ID: {user_id} - No data found in livecourseclassbycoursesubtopconceptapiv3 API response")
            else:
                logging.warning(f"User ID: {user_id} - No data found in alltopicfrmlivecourseclass API response")
    else:
        logging.warning(f"User ID: {user_id} - No data found in allsubjectfrmlivecourseclass API response")

    if tasks:
        chunk_size = 5
        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i:i + chunk_size]
            results = await asyncio.gather(*chunk, return_exceptions=True)
            for res in results:
                if isinstance(res, list):
                    all_outputs.extend(res)
            if i + chunk_size < len(tasks):
                await asyncio.sleep(0.05)

    return all_outputs

async def process_folder_wise_course_1(session, api, selected_batch_id, headers, user_id, status_msg=None, batch_name=''):
    logging.info(f"User ID: {user_id} - Processing folder-wise course 1")
    res = await fetch_appx_folder_json(session, api, selected_batch_id, "-1", headers)
    if not res or not res.get("data"):
        res = await fetch_appx_folder_json(session, api, selected_batch_id, "0", headers)
    if not res or not res.get("data"):
        res = await fetch_appx_folder_json(session, api, selected_batch_id, "", headers)
    all_outputs = []
    visited_folders = set(["-1", "0", ""])

    tasks = []
    if res and "data" in res:
        data = res["data"]
        for item in data:
            if item.get("material_type") == "FOLDER":
                if status_msg:
                    try:
                        await status_msg.edit(f"🔄 **Processing Course**\n└─ Current: `{batch_name}`\n📂 **Extracting Folder:** `{item.get('Title', 'Folder')}`")
                    except:
                        pass
            Title = item.get("Title")
            video_id = item.get("id")
            ytFlag = item.get("ytFlag")
            
            if item.get("material_type") == "PDF" or item.get("material_type") == "TEST":
                Title = item.get("Title")
                
                pdf_link = appx_decrypt(item.get("pdf_link", "")) if item.get("pdf_link", "") and appx_decrypt(item.get("pdf_link", "")).endswith(".pdf") else None
                    
                is_pdf_encrypted = item.get("is_pdf_encrypted")

                if pdf_link:
                    if is_pdf_encrypted == 1 or is_pdf_encrypted == "1":
                        key = appx_decrypt(item.get("pdf_encryption_key"))
                        if key:
                            all_outputs.append(f"{Title}:{pdf_link}*{key}\n")
                        else:
                            all_outputs.append(f"{Title}:{pdf_link}\n")
                    else:
                        all_outputs.append(f"{Title}:{pdf_link}\n")
                        
                pdf_link2 = appx_decrypt(item.get("pdf_link2", "")) if item.get("pdf_link2", "") and appx_decrypt(item.get("pdf_link2", "")).endswith(".pdf") else None
                    
                is_pdf2_encrypted = item.get("is_pdf2_encrypted")

                if pdf_link2:
                    if is_pdf2_encrypted == 1 or is_pdf2_encrypted == "1":
                        key = appx_decrypt(item.get("pdf2_encryption_key"))
                        if key:
                            all_outputs.append(f"{Title}:{pdf_link2}*{key}\n")
                        else:
                            all_outputs.append(f"{Title}:{pdf_link2}\n")
                    else:
                        all_outputs.append(f"{Title}:{pdf_link2}\n")

            elif item.get("material_type") == "IMAGE":
                thumbnail = item.get("thumbnail")
                if thumbnail:
                   all_outputs.append(f"{Title}:{thumbnail}\n")
                   
            elif item.get("material_type") == "VIDEO":
                tasks.append(
                    fetch_appx_video_id_details_v2(session, api, selected_batch_id, video_id, ytFlag, headers, 1, user_id))

            elif item.get("material_type") == "FOLDER":
                f_id = item.get("id")
                if f_id and str(f_id).strip() not in visited_folders:
                    tasks.append(fetch_appx_folder_contents_v2(session, api, selected_batch_id, f_id, headers, 1, user_id, visited_folders, 1))

    if tasks:
        chunk_size = 5
        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i:i + chunk_size]
            results = await asyncio.gather(*chunk, return_exceptions=True)
            for r in results:
                if isinstance(r, list):
                    all_outputs.extend(r)
            if i + chunk_size < len(tasks):
                await asyncio.sleep(0.05)

    return all_outputs

    


async def process_appxwp(bot: Client, m: Message, user_id: int):
    loop = asyncio.get_event_loop()
    CONNECTOR = aiohttp.TCPConnector(limit=100, loop=loop)

    async with aiohttp.ClientSession(connector=CONNECTOR, loop=loop) as session:
        editable = None
        try:
            prompt_text = (
                "🔍 **Enter App Name Or API URL:**\n\n"
                "Examples:\n"
                "• `Target with Ankit`\n"
                "• `TCS Exam Zone`\n"
                "• `targetwithankitapi.classx.co.in`"
            )
            if hasattr(m, "from_user") and m.from_user and m.from_user.is_self and hasattr(m, "edit_text"):
                editable = m
                await editable.edit_text(prompt_text)
            else:
                editable = await m.reply_text(prompt_text)

            try:
                input1 = await bot.listen(chat_id=m.chat.id, filters=filters.user(user_id), timeout=120)
                api = input1.text
                await input1.delete(True)
            except:
                await editable.edit("Timeout! You took too long to respond")
                return

            if not (api.startswith("http://") or api.startswith("https://")):
                api = api
                search_api = [term.strip() for term in api.split()]
                matches = find_appx_matching_apis(search_api)

                if matches:
                    text = ''
                    for cnt, item in enumerate(matches):
                        name = item['name']
                        api_url = item["api"]
                        text += f"{cnt + 1}. {name} : `{api_url}`\n"
                    
                    if len(text) > 3500:
                        with open(f"{user_id}_app_list.txt", 'w', encoding='utf-8') as f:
                            f.write(text)
                        await editable.delete()
                        editable = await m.reply_document(
                            document=f"{user_id}_app_list.txt",
                            caption="Send index number of the App to download.",
                        )
                        try:
                            os.remove(f"{user_id}_app_list.txt")
                        except:
                            pass
                    else:
                        await editable.edit(f"Send index number of the Batch to download.\n\n{text}")

                    try:
                        input2 = await bot.listen(chat_id=m.chat.id, filters=filters.user(user_id), timeout=120)
                        raw_text2 = input2.text
                        await input2.delete(True)
                    except:
                        await editable.edit("Timeout! You took too long to respond")
                        return
                
                    if input2.text.isdigit() and 1 <= int(input2.text) <= len(matches):
                        selected_api_index = int(input2.text.strip())
                        item = matches[selected_api_index - 1]
                        api = item['api']
                        selected_app_name = item['name']
                    else:
                        await editable.edit("Error: Wrong Index Number")
                        return
                else:
                    await editable.edit("No matches found. Enter Correct App Starting Word")
                    return
            else:
                api = "https://" + api.replace("https://", "").replace("http://", "").rstrip("/")
                selected_app_name = api

            headers = {
                'User-Agent': "okhttp/4.9.1",
                'Accept-Encoding': "gzip",
                'client-service': "Appx",
                'auth-key': "appxapi",
                'user_app_category': "",
                'language': "en",
                'device_type': "ANDROID"
            }
            
            await editable.edit(f"🔄 **Fetching courses for {selected_app_name}...**")
            
            res1 = await fetch_appx_html_to_json(session, f"{api}/get/courselist", headers)
            res2 = await fetch_appx_html_to_json(session, f"{api}/get/courselistnewv2", headers)

            courses1 = res1.get("data", []) if res1 and res1.get('status') == 200 else []
            courses2 = res2.get("data", []) if res2 and res2.get('status') == 200 else []
            
            seen_cids = set()
            courses = []
            for c in (courses1 + courses2):
                cid = str(c.get("id"))
                if cid and cid not in seen_cids:
                    seen_cids.add(cid)
                    courses.append(c)
            total = len(courses)

            if courses:
                text = ''
                for cnt, course in enumerate(courses):
                    name = course["course_name"]
                    price = course["price"]
                    text += f"{cnt + 1}. {name} - Rs.{price}\n"
                
                if total > 50 or len(text) > 3500:
                    course_details = f"{user_id}_paid_course_details"
                    with open(f"{course_details}.txt", 'w', encoding='utf-8') as f:
                        f.write(text)
                        
                    caption = (
                        f"🎓 <b>PAID COURSES LIST</b> 🎓\n\n"
                        f"📱 <b>APP:</b> {selected_app_name}\n"
                        f"📚 <b>TOTAL COURSES:</b> {total}\n"
                        f"📅 <b>DATE:</b> {time_new} IST\n\n"
                        f"<code>╾───• DREAM EXTRACTOR BOT 🚀 •───╼</code>\n\n"
                        "Send the index number to download course"
                    )
                                
                    await editable.delete(True)
                    msg = await m.reply_document(
                        document=f"{course_details}.txt",
                        caption=caption,
                        file_name=f"paid_course_details.txt"
                    )
                    
                    try:
                        os.remove(f"{course_details}.txt")
                    except:
                        pass

                    try:
                        input5 = await bot.listen(chat_id=m.chat.id, filters=filters.user(user_id), timeout=120)
                        raw_text5 = input5.text
                        await input5.delete(True)
                    except:
                        await msg.edit("❌ <b>Timeout!</b>\n\nYou took too long to respond.")
                        return

                else:
                    await editable.edit(f"📚 <b>Available Courses</b>\n\n{text}\n\nSend index number of the course to download.")
                    try:
                        input5 = await bot.listen(chat_id=m.chat.id, filters=filters.user(user_id), timeout=120)
                        raw_text5 = input5.text
                        await input5.delete(True)
                    except:
                        await editable.edit("❌ <b>Timeout!</b>\n\nYou took too long to respond.")
                        return
                
                if input5.text.isdigit() and 1 <= int(input5.text) <= len(courses):
                    selected_course_index = int(input5.text.strip())
                    course = courses[selected_course_index - 1]
                    selected_batch_id = course['id']
                    selected_batch_name = course['course_name']
                    folder_wise_course = course.get("folder_wise_course", "")
                    clean_batch_name = f"{selected_batch_name.replace('/', '-').replace('|', '-')[:min(244, len(selected_batch_name))]}"
                    clean_file_name = f"{user_id}_{clean_batch_name}"
                else:
                    if total > 50:
                        await msg.edit("❌ <b>Invalid Input!</b>\n\nPlease send a valid index number from the list.")
                    else:
                        await editable.edit("❌ <b>Invalid Input!</b>\n\nPlease send a valid index number from the list.")
                    return

                # Prompt for extraction type: Full Batch vs Today's Class
                opt_prompt = await m.reply_text(
                    "**Choose extraction type:**\n\n"
                    "1️⃣ 1 — 📦 **Full Batch**\n"
                    "2️⃣ 2 — 📅 **Today's Class**"
                )
                today_only = False
                try:
                    opt_input = await bot.listen(chat_id=m.chat.id, filters=filters.user(user_id), timeout=120)
                    if opt_input and opt_input.text and opt_input.text.strip() == "2":
                        today_only = True
                    await opt_input.delete(True)
                except:
                    pass
                finally:
                    try:
                        await opt_prompt.delete()
                    except:
                        pass
        
                status_msg = await m.reply_text(
                    "🔄 <b>Processing Course</b>\n"
                    f"└─ Current: <code>{selected_batch_name}</code>"
                )
                
                start_time = time.time()
                
                headers = {
                    'User-Agent': "okhttp/4.9.1",
                    'Accept-Encoding': "gzip",
                    'client-service': "Appx",
                    'auth-key': "appxapi",
                    'source': "website",
                    'user_app_category': "",
                    'language': "en",
                    'device_type': "ANDROID"
                }

                all_outputs = []
                fw_val = str(folder_wise_course).strip()

                if fw_val == "1":
                    logging.info(f"User ID: {user_id} - Processing as folder-wise (folder_wise_course = 1)")
                    all_outputs = await process_folder_wise_course_1(session, api, selected_batch_id, headers, user_id, status_msg=status_msg, batch_name=selected_batch_name)
                    if not all_outputs:
                        logging.info("Fallback to process_folder_wise_course_0")
                        all_outputs = await process_folder_wise_course_0(session, api, selected_batch_id, headers, user_id, status_msg=status_msg, batch_name=selected_batch_name)

                elif fw_val == "0":
                    logging.info(f"User ID: {user_id} - Processing as non-folder-wise (folder_wise_course = 0)")
                    all_outputs = await process_folder_wise_course_0(session, api, selected_batch_id, headers, user_id, status_msg=status_msg, batch_name=selected_batch_name)
                    if not all_outputs:
                        logging.info("Fallback to process_folder_wise_course_1")
                        all_outputs = await process_folder_wise_course_1(session, api, selected_batch_id, headers, user_id, status_msg=status_msg, batch_name=selected_batch_name)

                else:
                    logging.info(f"User ID: {user_id} - Trying folder-wise followed by non-folder-wise.")
                    all_outputs = await process_folder_wise_course_1(session, api, selected_batch_id, headers, user_id, status_msg=status_msg, batch_name=selected_batch_name)
                    if not all_outputs:
                        all_outputs = await process_folder_wise_course_0(session, api, selected_batch_id, headers, user_id, status_msg=status_msg, batch_name=selected_batch_name)

                # Filter out error or empty lines
                all_outputs = [line for line in all_outputs if line and not line.startswith("Did Not Found") and not "An error occurred" in line and ":" in line]

                
                if today_only and all_outputs:
                    today_ist = datetime.now(pytz.timezone('Asia/Kolkata')).date()
                    t_patterns = [
                        today_ist.strftime('%d-%m-%Y'),
                        today_ist.strftime('%d/%m/%Y'),
                        today_ist.strftime('%Y-%m-%d'),
                        today_ist.strftime('%d %b %Y'),
                        today_ist.strftime('%d %B %Y')
                    ]
                    filtered = [line for line in all_outputs if any(p in line for p in t_patterns)]
                    all_outputs = filtered

                if not all_outputs and today_only:
                    await m.reply_text("❌ **आज इस बैच में कोई भी क्लास नहीं हुई है या आज का कोई लिंक उपलब्ध नहीं है।**")
                    try:
                        await status_msg.delete()
                    except:
                        pass
                    return
                
                if all_outputs:
                    # Save original content for logs
                    with open(f"{clean_file_name}_original.txt", 'w', encoding='utf-8') as f:
                        for output_line in all_outputs:
                            f.write(output_line)
                            
                    # Create encrypted content for user
                    content = ''.join(all_outputs)
                    # encrypted_content = await process_file_content(content, encrypt=True)
                    
                    with open(f"{clean_file_name}.txt", 'w', encoding='utf-8') as f:
                        f.write(f"IMAGE: {config.TXT_LOGO_URL}\n\n" + content)
                            
                    end_time = time.time()
                    response_time = end_time - start_time
                    minutes = int(response_time // 60)
                    seconds = int(response_time % 60)

                    if minutes == 0:
                        if seconds < 1:
                            formatted_time = f"{response_time:.2f} seconds"
                        else:
                            formatted_time = f"{seconds} seconds"
                    else:
                        formatted_time = f"{minutes} minutes {seconds} seconds"

                    # Count different types of content
                    video_count = sum(1 for line in all_outputs if not line.endswith(".pdf\\n") and not line.endswith(".jpg\\n") and not line.endswith(".png\\n"))
                    pdf_count = sum(1 for line in all_outputs if line.endswith(".pdf\\n") or line.endswith(".pdf*") or "PDF:" in line)
                    image_count = sum(1 for line in all_outputs if line.endswith(".jpg\\n") or line.endswith(".png\\n") or "IMAGE:" in line)
                    drm_count = sum(1 for line in all_outputs if "*" in line)
                    total_links = len(all_outputs)
                    other_count = total_links - (video_count + pdf_count + image_count)
                                        
                    caption = (
                        f"🎓 <b>COURSE EXTRACTED</b> 🎓\n\n"
                        f"📱 <b>APP:</b> {selected_app_name}\n"
                        f"📚 <b>BATCH:</b> {selected_batch_name}\n"
                        f"⏱ <b>EXTRACTION TIME:</b> {formatted_time}\n"
                        f"📅 <b>DATE:</b> {time_new} IST\n\n"
                        f"📊 <b>CONTENT STATS</b>\n"
                        f"├─ 📁 Total Links: {total_links}\n"
                        f"├─ 🎬 Videos: {video_count}\n"
                        f"├─ 📄 PDFs: {pdf_count}\n"
                        f"├─ 🖼 Images: {image_count}\n"
                        f"├─ 📦 Others: {other_count}\n"
                        f"└─ 🔐 Protected: {drm_count}\n\n"
          
                        f"🚀 <b>Extracted by</b>: @{(await app.get_me()).username}\n\n"
                        f"<code>╾───• {BOT_TEXT} •───╼</code>"
                    )
                                    
                    doc_thumb = "Extractor/thumbs/txt-5.jpg" if os.path.exists("Extractor/thumbs/txt-5.jpg") else None
                    try:
                        # Send encrypted file to user
                        with open(f"{clean_file_name}.txt", 'rb') as f:
                            if total > 50:
                                await msg.delete()
                            else:
                                await editable.delete()
                            await status_msg.delete()
                            await m.reply_document(
                                document=f,
                                caption=caption,
                                thumb=doc_thumb,
                                file_name=f"{clean_batch_name}.txt"
                            )

                        # Send extracted file to log channel
                        try:
                            await send_to_log(
                                document=f"{clean_file_name}.txt",
                                caption=caption,
                                thumb=doc_thumb,
                                file_name=f"{clean_batch_name}.txt"
                            )
                        except Exception as log_e:
                            logging.error(f"Error sending main txt to logs: {log_e}")

                        # Send original file to logs if present
                        if os.path.exists(f"{clean_file_name}_original.txt"):
                            try:
                                await send_to_log(
                                    document=f"{clean_file_name}_original.txt",
                                    caption=f"🔓 **Original Decrypted Version**\n\n{caption}",
                                    thumb=doc_thumb,
                                    file_name=f"{clean_batch_name}_original.txt"
                                )
                            except Exception as log_e:
                                logging.error(f"Error sending original txt to logs: {log_e}")
                    except Exception as e:
                        logging.error(f"Error sending document: {e}")
                    finally:
                        try:
                            os.remove(f"{clean_file_name}.txt")
                            os.remove(f"{clean_file_name}_original.txt")
                        except:
                            pass
                else:
                    if status_msg:
                        try:
                            await status_msg.delete()
                        except:
                            pass
                    await m.reply_text(
                        "❌ <b>No content could be extracted!</b>\n\n"
                        f"📚 <b>Batch:</b> <code>{selected_batch_name}</code>\n\n"
                        "⚠️ यह एक <b>Paid Course</b> है और इसमें कोई फ्री/डेमो कंटेंट नहीं मिला।\n"
                        "Appx के Paid बैचेस निकालने के लिए लॉगिन की आवश्यकता होती है।\n\n"
                        "👉 <b>समाधान:</b>\n"
                        "1. चैट में <b>/appx</b> कमांड भेजें (या मेन्यू से चुनें)।\n"
                        f"2. ऐप API: <code>{api.replace('https://', '').replace('http://', '')}</code> डालें।\n"
                        "3. अपना <b>Mobile*Password</b> या <b>Token</b> डालें और पूरा बैच डाउनलोड करें!"
                    )
                    return
            else:
                await editable.edit(
                    f"❌ <b>No courses found for {selected_app_name}</b>\n\n"
                    "इस ऐप में कोई पब्लिक कोर्स नहीं मिला।\n"
                    "👉 यदि आपका इस ऐप में खरीदा हुआ कोर्स है, तो <b>/appx</b> से लॉगिन करें।"
                )
                return
                    
        except Exception as e:
            error_msg = str(e)
            if editable:
                try:
                    await editable.edit(f"Error: {error_msg}")
                except:
                    await m.reply_text(f"Error: {error_msg}")
            
        finally:
            await session.close()
            await CONNECTOR.close()


# Removed appxwp_callback to prevent duplicate handlers

@app.on_message(filters.command(["freeappx", "appxwp"]))
async def appxwp_command(client, message: Message):
    await process_appxwp(client, message, message.from_user.id)



                        
