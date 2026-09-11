import asyncio
import aiohttp
import json
import os
import base64
import time
import re
from datetime import datetime
from Extractor.core.utils import forward_to_log, send_to_log
import pytz
import config 
import logging
from Extractor import app
from config import PREMIUM_LOGS, join, BOT_TEXT

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

join = config.join
india_timezone = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(india_timezone)
time_new = current_time.strftime("%d-%m-%Y %I:%M %p")

# Pure Python AES-128-CBC Decryption Engine
Sbox = [
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
InvSbox = [0] * 256
for i, x in enumerate(Sbox):
    InvSbox[x] = i

Rcon = [0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36, 0x6C, 0xD8, 0xAB, 0x4D, 0x9A, 0x2F, 0x5E, 0xBC, 0x63, 0xC6, 0x97, 0x35, 0x6A, 0xD4, 0xB3, 0x7D, 0xFA, 0xEF, 0xC5, 0x91, 0x39]

def _sub_word(word): return [Sbox[b] for b in word]
def _rot_word(word): return word[1:] + word[:1]
def _key_expansion_128(key):
    w = [list(key[i:i+4]) for i in range(0, 16, 4)]
    for i in range(4, 44):
        temp = list(w[i - 1])
        if i % 4 == 0:
            temp = _sub_word(_rot_word(temp))
            temp[0] ^= Rcon[i // 4]
        w.append([w[i - 4][j] ^ temp[j] for j in range(4)])
    return w

def _inv_sub_bytes(state):
    for r in range(4):
        for c in range(4): state[r][c] = InvSbox[state[r][c]]

def _inv_shift_rows(state):
    state[1] = state[1][-1:] + state[1][:-1]
    state[2] = state[2][-2:] + state[2][:-2]
    state[3] = state[3][-3:] + state[3][:-3]

def _gmul(a, b):
    p = 0
    for _ in range(8):
        if b & 1: p ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi: a ^= 0x1B
        b >>= 1
    return p

def _inv_mix_columns(state):
    for c in range(4):
        a0, a1, a2, a3 = state[0][c], state[1][c], state[2][c], state[3][c]
        state[0][c] = _gmul(0x0e, a0) ^ _gmul(0x0b, a1) ^ _gmul(0x0d, a2) ^ _gmul(0x09, a3)
        state[1][c] = _gmul(0x09, a0) ^ _gmul(0x0e, a1) ^ _gmul(0x0b, a2) ^ _gmul(0x0d, a3)
        state[2][c] = _gmul(0x0d, a0) ^ _gmul(0x09, a1) ^ _gmul(0x0e, a2) ^ _gmul(0x0b, a3)
        state[3][c] = _gmul(0x0b, a0) ^ _gmul(0x0d, a1) ^ _gmul(0x09, a2) ^ _gmul(0x0e, a3)

def _add_round_key(state, round_key):
    for r in range(4):
        for c in range(4): state[r][c] ^= round_key[c][r]

def _decrypt_block_128(block, round_keys):
    state = [[block[r + 4 * c] for c in range(4)] for r in range(4)]
    _add_round_key(state, round_keys[40:44])
    for rnd in range(9, 0, -1):
        _inv_shift_rows(state)
        _inv_sub_bytes(state)
        _add_round_key(state, round_keys[rnd*4 : rnd*4+4])
        _inv_mix_columns(state)
    _inv_shift_rows(state)
    _inv_sub_bytes(state)
    _add_round_key(state, round_keys[0:4])
    return bytes([state[r][c] for c in range(4) for r in range(4)])

def _pure_aes_cbc_decrypt(ciphertext, key=b"638udh3829162018", iv=b"fedcba9876543210"):
    if len(ciphertext) % 16 != 0: return b""
    round_keys = _key_expansion_128(key)
    plaintext = bytearray()
    prev = iv
    for i in range(0, len(ciphertext), 16):
        block = ciphertext[i:i+16]
        dec = _decrypt_block_128(block, round_keys)
        pt = bytes([dec[j] ^ prev[j] for j in range(16)])
        plaintext.extend(pt)
        prev = block
    if plaintext:
        pad_len = plaintext[-1]
        if 1 <= pad_len <= 16 and plaintext[-pad_len:] == bytes([pad_len]*pad_len):
            plaintext = plaintext[:-pad_len]
    return bytes(plaintext)

def parse_json_safe(text):
    """Safely extract and parse JSON even if server returns PHP errors or HTML."""
    if not text or not isinstance(text, str):
        return None
    clean = text.strip()
    try:
        return json.loads(clean)
    except Exception:
        pass
    first_brace = clean.find("{")
    first_bracket = clean.find("[")
    start_idx = -1
    if first_brace != -1 and first_bracket != -1:
        start_idx = min(first_brace, first_bracket)
    elif first_brace != -1:
        start_idx = first_brace
    elif first_bracket != -1:
        start_idx = first_bracket
    if start_idx != -1:
        candidate = clean[start_idx:]
        try:
            return json.loads(candidate)
        except Exception:
            pass
        last_brace = candidate.rfind("}")
        last_bracket = candidate.rfind("]")
        end_idx = max(last_brace, last_bracket)
        if end_idx != -1:
            try:
                return json.loads(candidate[:end_idx+1])
            except Exception:
                pass
    return None

def decrypt(enc):
    """Universal AES-128-CBC Decryptor for Appx / ClassX."""
    if not enc or not isinstance(enc, str):
        return ""
    enc_clean = enc.strip()
    if enc_clean.startswith("http://") or enc_clean.startswith("https://"):
        return enc_clean
    iv = b'fedcba9876543210'
    enc_part = enc_clean
    if ':' in enc_clean:
        parts = enc_clean.split(':', 1)
        enc_part = parts[0].strip()
        try:
            custom_iv = base64.b64decode(parts[1].strip())
            if len(custom_iv) == 16:
                iv = custom_iv
        except Exception:
            pass
    # 1. Try PyCryptodome if present
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        enc_bytes = base64.b64decode(enc_part)
        if len(enc_bytes) > 0:
            key = b'638udh3829162018'
            cipher = AES.new(key, AES.MODE_CBC, iv)
            plaintext = unpad(cipher.decrypt(enc_bytes), AES.block_size)
            res = plaintext.decode('utf-8', errors='ignore').strip()
            if res:
                return res
    except Exception:
        pass
    # 2. Pure Python fallback (works anywhere without dependencies)
    try:
        enc_bytes = base64.b64decode(enc_part)
        dec_bytes = _pure_aes_cbc_decrypt(enc_bytes, b'638udh3829162018', iv)
        res = dec_bytes.decode('utf-8', errors='ignore').strip()
        if res:
            return res
    except Exception:
        pass
    return enc_clean

def decode_base64(encoded_str):
    """Decode base64 encoded string."""
    try:
        decoded_bytes = base64.b64decode(encoded_str)
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        return ""

def is_today_mix_item(item_obj, data_obj=None):
    today_ist = datetime.now(pytz.timezone('Asia/Kolkata')).date()
    objs = [item_obj]
    if data_obj and isinstance(data_obj, dict):
        objs.append(data_obj)
    date_fields = ["created_at", "createdAt", "start_date", "startDate", "live_date", "liveDate", "date", "PublishDate", "publish_date", "schedule_date", "event_date"]
    for obj in objs:
        if not isinstance(obj, dict):
            continue
        for fld in date_fields:
            val = obj.get(fld)
            if not val:
                continue
            val_str = str(val)
            if today_ist.strftime('%Y-%m-%d') in val_str or today_ist.strftime('%d-%m-%Y') in val_str or today_ist.strftime('%d/%m/%Y') in val_str:
                return True
            try:
                num = float(val)
                if num > 1e11:
                    num = num / 1000.0
                dt = datetime.fromtimestamp(num, tz=pytz.timezone('Asia/Kolkata')).date()
                if dt == today_ist:
                    return True
            except:
                pass
    return False

async def fetch_item_details(session, api_base, course_id, item, headers, today_only=False):
    """Fetch details for a single item (video/pdf/image) including DRM, HLS, and encrypted streams."""
    try:
        if not item or not isinstance(item, dict):
            return []
            
        mtype = str(item.get("material_type", "")).upper()
        if mtype == "FOLDER":
            return []

        outputs = []
        data = dict(item)
        fi = item.get("id") or item.get("video_id")

        # Fast check: if item doesn't have direct link, query video details
        has_direct_link = bool(
            item.get("download_link") or item.get("file_link") or 
            item.get("pdf_link") or item.get("download_links") or
            item.get("video_player_url") or item.get("recording_hls")
        )
        if not has_direct_link and fi:
            for folder_wise in [1, 0]:
                try:
                    async with session.get(
                        f"{api_base}/get/fetchVideoDetailsById?course_id={course_id}&folder_wise_course={folder_wise}&ytflag=0&video_id={fi}",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            raw_resp = await response.text()
                            r4 = parse_json_safe(raw_resp)
                            if r4 and isinstance(r4, dict) and r4.get("data"):
                                data.update(r4["data"])
                                break
                except Exception:
                    pass

        if today_only and not is_today_mix_item(item, data):
            return []

        vt = data.get("Title") or item.get("Title") or data.get("title") or item.get("title") or "Lecture"
        vt = str(vt).strip().replace("\n", " ")

        # 1. YouTube Link
        if data.get("ytFlag") in [1, "1", True] or data.get("ytflag") in [1, "1", True]:
            yt_id = data.get("youtube_id") or data.get("video_id") or data.get("id") or data.get("embed_url") or ""
            if yt_id:
                yt_str = str(yt_id).strip()
                dec_yt = decrypt(yt_str)
                if len(dec_yt) == 11 and " " not in dec_yt:
                    outputs.append(f"{vt}:https://youtu.be/{dec_yt}")
                elif yt_str.isalnum() and len(yt_str) == 11:
                    outputs.append(f"{vt}:https://youtu.be/{yt_str}")
                elif "youtube.com" in dec_yt or "youtu.be" in dec_yt:
                    outputs.append(f"{vt}:{dec_yt}")

        # 2. Direct Video Download Link or File Link
        video_found = False
        vl = data.get("download_link") or item.get("download_link") or data.get("download_link2") or ""
        stream_url = (
            data.get("file_link") or data.get("stream_url") or data.get("video_url") or 
            data.get("url") or item.get("file_link") or item.get("stream_url") or 
            data.get("video_player_url") or data.get("video_player_lower_url") or
            data.get("download_url_higher_version") or data.get("download_url_lower_version") or
            data.get("recording_hls") or ""
        )
        
        # Fallback to download_links bitrate array if primary is empty
        if not vl and not stream_url:
            dl_array = data.get("download_links") or item.get("download_links") or []
            if isinstance(dl_array, list) and dl_array:
                for dl_obj in dl_array:
                    if isinstance(dl_obj, dict) and dl_obj.get("path"):
                        vl = dl_obj["path"]
                        break

        if vl:
            dvl = decrypt(str(vl))
            if dvl and ("http" in dvl or ".mpd" in dvl or ".m3u8" in dvl or ".mp4" in dvl or ".pdf" in dvl):
                if ".pdf" in dvl.lower():
                    outputs.append(f"{vt} PDF:{dvl}")
                else:
                    outputs.append(f"{vt}:{dvl}")
                video_found = True
        elif stream_url:
            ds = decrypt(str(stream_url))
            if ds and ("http" in ds or ".mpd" in ds or ".m3u8" in ds or ".mp4" in ds or ".pdf" in ds):
                if ".pdf" in ds.lower():
                    outputs.append(f"{vt} PDF:{ds}")
                else:
                    outputs.append(f"{vt}:{ds}")
                video_found = True

        # 3. Encrypted links & WebDRM links
        if not video_found:
            enc_links = data.get("encrypted_links") or item.get("encrypted_links") or []
            if isinstance(enc_links, list):
                for link in enc_links:
                    if not isinstance(link, dict):
                        continue
                    a = link.get("path") or link.get("url") or link.get("link")
                    k = link.get("key")
                    if a and k:
                        k1 = decrypt(str(k))
                        k2 = decode_base64(k1) if k1 else ""
                        da = decrypt(str(a))
                        if da:
                            if k2:
                                outputs.append(f"{vt}:{da}*{k2}")
                            else:
                                outputs.append(f"{vt}:{da}")
                            video_found = True
                            break
                    elif a:
                        da = decrypt(str(a))
                        if da:
                            outputs.append(f"{vt}:{da}")
                            video_found = True
                            break

        # 4. ClassX MPD DRM Links fallback
        if not video_found and fi and mtype in ["VIDEO", "LIVE", ""]:
            for fw in [1, 0]:
                try:
                    async with session.get(
                        f"{api_base}/get/get_mpd_drm_links?videoid={fi}&folder_wise_course={fw}",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=4)
                    ) as drm_res:
                        if drm_res.status == 200:
                            raw_drm = await drm_res.text()
                            drm_json = parse_json_safe(raw_drm)
                            if drm_json and isinstance(drm_json, dict) and drm_json.get("data"):
                                drm_list = drm_json["data"]
                                if isinstance(drm_list, list) and len(drm_list) > 0:
                                    drm_path = drm_list[0].get("path", "")
                                    if drm_path:
                                        dec_path = decrypt(drm_path)
                                        if dec_path:
                                            outputs.append(f"{vt}:{dec_path}")
                                            video_found = True
                                            break
                except Exception:
                    pass

        # 5. PDF Links
        for pdf_num in range(1, 4):
            key_suffix = '' if pdf_num == 1 else str(pdf_num)
            pdf_link = data.get(f"pdf_link{key_suffix}") or data.get(f"pdf{key_suffix}_link") or item.get(f"pdf_link{key_suffix}") or ""
            pdf_key = data.get(f"pdf{'_' if pdf_num == 1 else str(pdf_num)}_encryption_key") or data.get(f"pdf_encryption_key{key_suffix}") or item.get(f"pdf_encryption_key{key_suffix}") or ""
            
            if pdf_link:
                dp = decrypt(str(pdf_link))
                dpk = decrypt(str(pdf_key)) if pdf_key else ""
                if dp and ("http" in dp or ".pdf" in dp.lower()):
                    label = f"{vt} PDF" if pdf_num == 1 else f"{vt} PDF{pdf_num}"
                    is_enc = str(data.get(f"is_pdf{key_suffix}_encrypted", item.get(f"is_pdf{key_suffix}_encrypted", "0")))
                    if (is_enc == "1" or dpk) and dpk and dpk != "abcdefg":
                        outputs.append(f"{label}:{dp}*{dpk}")
                    else:
                        outputs.append(f"{label}:{dp}")

        # 6. Image material type
        if mtype == "IMAGE":
            thumb = item.get("thumbnail") or data.get("thumbnail")
            if thumb:
                outputs.append(f"{vt} IMAGE:{thumb}")

        return outputs

    except Exception as e:
        logger.error(f"Error fetching item details: {e}")
        return []

async def fetch_folder_json(session, api_base, course_id, folder_id, headers):
    """Query folder contents across multiple possible Appx/ClassX endpoints."""
    search_ids = [str(folder_id)]
    if str(folder_id) in ["-1", "0", ""]:
        search_ids = ["-1", "0", ""]

    for fid in search_ids:
        endpoints = [
            f"/get/folder_contentsv3?course_id={course_id}&parent_id={fid}&windowsapp=true&start=-1",
            f"/get/folder_contentsv3?course_id={course_id}&parent_id={fid}&windowsapp=true&start=0",
            f"/get/folder_contentsv3?course_id={course_id}&parent_id={fid}&start=-1",
            f"/get/folder_contentsv3?course_id={course_id}&parent_id={fid}&start=0",
            f"/get/folder_contentsv3?course_id={course_id}&parent_id={fid}",
            f"/get/folder_contentsv2?course_id={course_id}&parent_id={fid}&start=-1",
            f"/get/folder_contentsv2?course_id={course_id}&parent_id={fid}&start=0",
            f"/get/folder_contentsv2?course_id={course_id}&parent_id={fid}",
            f"/get/folder_contents?course_id={course_id}&parent_id={fid}",
            f"/get/parent_folder_contents?course_id={course_id}&current_folder_id={fid}"
        ]
        for endpoint in endpoints:
            try:
                async with session.get(f"{api_base}{endpoint}", headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as res:
                    if res.status == 200:
                        text = await res.text()
                        if text:
                            j = parse_json_safe(text)
                            if j and isinstance(j, dict) and j.get("data"):
                                return j
            except Exception:
                pass
    return {}

async def fetch_folder_contents(session, api_base, course_id, folder_id, headers, visited_folders=None, depth=0, today_only=False):
    """Recursively and concurrently fetch contents of a folder and its subfolders."""
    if visited_folders is None:
        visited_folders = set()

    fid_str = str(folder_id).strip()
    if not fid_str or fid_str in visited_folders or depth > 15:
        return []
    visited_folders.add(fid_str)

    try:
        outputs = []
        j = await fetch_folder_json(session, api_base, course_id, folder_id, headers)
        
        if j and "data" in j and isinstance(j["data"], list):
            tasks = []
            for item in j["data"]:
                mtype = str(item.get("material_type", "")).upper()
                if mtype == "FOLDER":
                    sub_id = item.get("id")
                    if sub_id and str(sub_id).strip() not in visited_folders:
                        tasks.append(fetch_folder_contents(session, api_base, course_id, sub_id, headers, visited_folders, depth + 1, today_only=today_only))
                else:
                    tasks.append(fetch_item_details(session, api_base, course_id, item, headers, today_only=today_only))

            if tasks:
                chunk_size = 8
                for i in range(0, len(tasks), chunk_size):
                    chunk = tasks[i:i + chunk_size]
                    results = await asyncio.gather(*chunk, return_exceptions=True)
                    for res in results:
                        if isinstance(res, list):
                            outputs.extend(res)

        return outputs

    except Exception as e:
        logger.error(f"Error fetching folder contents: {e}")
        return []

async def fetch_subject_fallback(session, api_base, course_id, headers, today_only=False):
    """Fallback to extract subjects & topics if folder contents return empty."""
    outputs = []
    try:
        url = f"{api_base}/get/allsubjectfrmlivecourseclass?courseid={course_id}&start=-1"
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as res:
            if res.status == 200:
                raw_text = await res.text()
                data = parse_json_safe(raw_text)
                if data and isinstance(data, dict) and data.get("data"):
                    for subject in data["data"]:
                        si = subject.get("subjectid") or subject.get("id")
                        if not si:
                            continue
                        topic_url = f"{api_base}/get/alltopicfrmlivecourseclass?courseid={course_id}&subjectid={si}&start=-1"
                        try:
                            async with session.get(topic_url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as tres:
                                if tres.status == 200:
                                    raw_t = await tres.text()
                                    tdata = parse_json_safe(raw_t)
                                    if tdata and isinstance(tdata, dict) and tdata.get("data"):
                                        for topic in tdata["data"]:
                                            ti = topic.get("topicid") or topic.get("id")
                                            vid_url = f"{api_base}/get/livecourseclassbycoursesubtopconceptapiv3?courseid={course_id}&subjectid={si}&topicid={ti}&conceptid=&start=-1"
                                            try:
                                                async with session.get(vid_url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as vres:
                                                    if vres.status == 200:
                                                        raw_v = await vres.text()
                                                        vdata = parse_json_safe(raw_v)
                                                        if vdata and isinstance(vdata, dict) and vdata.get("data"):
                                                            for item in vdata["data"]:
                                                                item_lines = await fetch_item_details(session, api_base, course_id, item, headers, today_only=today_only)
                                                                if item_lines:
                                                                    outputs.extend(item_lines)
                                            except Exception:
                                                pass
                        except Exception:
                            pass
    except Exception:
        pass
    return outputs

async def fetch_course_by_id_fallback(session, api_base, course_id, headers, today_only=False):
    """Fallback to extract via course_by_id if folder and subject endpoints return empty."""
    outputs = []
    try:
        url = f"{api_base}/get/course_by_id?id={course_id}"
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as res:
            if res.status == 200:
                raw = await res.text()
                data = parse_json_safe(raw)
                if data and isinstance(data, dict) and data.get("data"):
                    cdata = data["data"]
                    subjects = cdata.get("subject") or []
                    for s in subjects:
                        if not isinstance(s, dict):
                            continue
                        topics = s.get("topic") or []
                        for t in topics:
                            if not isinstance(t, dict):
                                continue
                            classes = t.get("class") or []
                            for item in classes:
                                if isinstance(item, dict):
                                    item_lines = await fetch_item_details(session, api_base, course_id, item, headers, today_only=today_only)
                                    if item_lines:
                                        outputs.extend(item_lines)
    except Exception:
        pass
    return outputs

async def v2_new(app, message, token, userid, hdr1, app_name, raw_text2, api_base, sanitized_course_name, start_time, start, end, pricing, input2, m1, m2, today_only=False):
    """Process and extract course content."""
    try:
        progress_msg = await message.reply_text(
            "🔄 <b>Processing Large Batch</b>\n"
            f"└─ Initializing batch: <code>{sanitized_course_name}</code>"
        )

        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Recursively fetch all contents from root folder (-1, fallback 0)
            visited = set()
            all_outputs = await fetch_folder_contents(session, api_base, raw_text2, "-1", hdr1, visited_folders=visited, depth=0, today_only=today_only)

            if not all_outputs:
                visited = set()
                all_outputs = await fetch_folder_contents(session, api_base, raw_text2, "0", hdr1, visited_folders=visited, depth=0, today_only=today_only)

            if not all_outputs:
                visited = set()
                all_outputs = await fetch_folder_contents(session, api_base, raw_text2, "", hdr1, visited_folders=visited, depth=0, today_only=today_only)

            if not all_outputs:
                all_outputs = await fetch_subject_fallback(session, api_base, raw_text2, hdr1, today_only=today_only)

            if not all_outputs:
                all_outputs = await fetch_course_by_id_fallback(session, api_base, raw_text2, hdr1, today_only=today_only)

            if not all_outputs:
                if today_only:
                    await progress_msg.edit_text("❌ **आज इस बैच में कोई भी क्लास नहीं हुई है या आज का कोई लिंक उपलब्ध नहीं है।**")
                else:
                    await progress_msg.edit_text("❌ <b>No content found in this batch</b>\n\nइस बैच में कोई सक्रिय सामग्री या लिंक्स उपलब्ध नहीं हैं।")
                return

            # Count content types
            video_count = sum(1 for url in all_outputs if any(ext in url.lower() for ext in ['.mp4', '.m3u8', '.mpd']))
            pdf_count = sum(1 for url in all_outputs if '.pdf' in url.lower())
            encrypted_count = sum(1 for url in all_outputs if '*' in url)

            # Save content to file safely
            safe_app = re.sub(r'[^a-zA-Z0-9_-]', '_', str(app_name))
            safe_course = re.sub(r'[^a-zA-Z0-9_-]', '_', str(sanitized_course_name))[:35]
            file_name = f"{safe_app}_{safe_course}_{int(datetime.now().timestamp())}.txt"
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(f"IMAGE: {config.TXT_LOGO_URL}\n\n" + '\n'.join(all_outputs))

            # Calculate duration
            end_time = datetime.now()
            duration = end_time - datetime.fromtimestamp(start_time)
            minutes, seconds = divmod(duration.total_seconds(), 60)

            # Prepare caption
            batch_display_title = f"{sanitized_course_name} (Today's Class)" if today_only else sanitized_course_name
            if len(batch_display_title) > 60:
                batch_display_title = batch_display_title[:57] + "..."

            caption = (
                f"🎓 <b>COURSE EXTRACTED</b> 🎓\n\n"
                f"📱 <b>APP:</b> {app_name}\n"
                f"📚 <b>BATCH:</b> {batch_display_title}\n"
                f"⏱ <b>EXTRACTION TIME:</b> {int(minutes):02d}:{int(seconds):02d}\n"
                f"📅 <b>DATE:</b> {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y %H:%M:%S')} IST\n\n"
                f"📊 <b>CONTENT STATS</b>\n"
                f"├─ 📁 Total Links: {len(all_outputs)}\n"
                f"├─ 🎬 Videos: {video_count}\n"
                f"├─ 📄 PDFs: {pdf_count}\n"
                f"└─ 🔐 Encrypted: {encrypted_count}\n\n"
                f"🚀 <b>Extracted by:</b> @{(await app.get_me()).username}\n\n"
                f"<code>╾───• {BOT_TEXT} •───╼</code>"
            )
            if len(caption) > 1024:
                caption = caption[:1020]

            # Send file with multiple fallbacks
            doc_thumb = "Extractor/thumbs/txt-5.jpg" if os.path.exists("Extractor/thumbs/txt-5.jpg") else None
            try:
                await message.reply_document(
                    document=file_name,
                    caption=caption,
                    thumb=doc_thumb
                )
            except Exception as e_thumb:
                try:
                    await message.reply_document(
                        document=file_name,
                        caption=caption
                    )
                except Exception as e_direct:
                    try:
                        await app.send_document(
                            chat_id=message.chat.id,
                            document=file_name,
                            caption=caption
                        )
                    except Exception as e_app:
                        logger.error(f"Error sending document: {e_app}")
                        raise e_app

            try:
                await send_to_log(file_name, caption=caption, thumb=doc_thumb)
            except Exception as e:
                logger.error(f"Error logging file in mix.py: {e}")

            if os.path.exists(file_name):
                try:
                    os.remove(file_name)
                except Exception:
                    pass

            # Delete temporary messages
            for msg in [input2, m1, m2]:
                try:
                    await msg.delete()
                except:
                    pass

            await progress_msg.edit_text(
                "✅ <b>Extraction completed successfully!</b>\n\n"
                f"📊 𝗙𝗶𝗻𝗮𝗹 𝗦𝘁𝗮𝘁𝘂𝘀:\n"
                f"📚 Processed: {len(all_outputs)} items\n"
                f"📤 File has been uploaded\n\n"
                f"Thank you for using DREAM EXTRACTOR BOT 🚀! 🌟"
            )

    except Exception as e:
        logger.error(f"Error in v2_new: {e}")
        await message.reply_text(
            "❌ <b>An error occurred</b>\n\n"
            f"Error: <code>{str(e)}</code>\n\n"
            "Please try again or contact support."
        )
                              
