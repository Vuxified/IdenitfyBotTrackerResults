#!/usr/bin/env python3
import os
import asyncio
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError

# ─── load your .env right here ────────────────────────────────────────────────
load_dotenv()  
TELETHON_API_ID   = int(os.getenv("TELETHON_API_ID"))
TELETHON_API_HASH = os.getenv("TELETHON_API_HASH")

def main():
    # 1) start up Telethon (will prompt for phone & code once)
    client = TelegramClient('session', TELETHON_API_ID, TELETHON_API_HASH)
    client.connect()
    if not client.is_user_authorized():
        phone = input("Phone (+1…): ")
        client.send_code_request(phone)
        code = input("Code: ")
        try:
            client.sign_in(phone, code)
        except SessionPasswordNeededError:
            pw = input("2FA password: ")
            client.sign_in(password=pw)

    # 2) header
    print(f"{'Name':30} {'ID':15} {'Username'}")
    print("-" * 60)

    # 3) iterate & print
    for dialog in client.iter_dialogs():
        name     = dialog.name or "<no name>"
        chat_id  = dialog.id
        username = getattr(dialog.entity, "username", "")
        print(f"{name:30} {str(chat_id):15} {username}")

    client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
