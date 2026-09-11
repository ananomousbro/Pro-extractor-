import os

with open("Extractor/modules/appex_v4.py", "r") as f:
    content = f.read()

old_content = """                    if second_response.get("status") == 200 and "data" in second_response:
                        userid = str(second_response["data"].get("userid") or second_response["data"].get("id") or "")
                        token = second_response["data"].get("token")
                    else:
                        fail_msg = second_response.get("message") or response.get("message") or "Invalid credentials"
                        return await message.reply_text(f"❌ <b>Login Failed:</b> {fail_msg}")"""

new_content = """                    if second_response.get("status") == 200 and "data" in second_response:
                        userid = str(second_response["data"].get("userid") or second_response["data"].get("id") or "")
                        token = second_response["data"].get("token")
                    else:
                        data_phone = {"phone": email, "password": password}
                        res3 = requests.post(raw_url, data=data_phone, headers=headers).json()
                        if res3.get("status") == 200 and "data" in res3:
                            userid = str(res3["data"].get("userid") or res3["data"].get("id") or "")
                            token = res3["data"].get("token")
                        else:
                            fail_msg = res3.get("message") or second_response.get("message") or response.get("message") or "Invalid credentials"
                            return await message.reply_text(f"❌ <b>Login Failed:</b> {fail_msg}")"""

content = content.replace(old_content, new_content)

with open("Extractor/modules/appex_v4.py", "w") as f:
    f.write(content)

