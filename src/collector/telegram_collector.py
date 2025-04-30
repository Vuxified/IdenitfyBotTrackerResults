#!/usr/bin/env python3
import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import boto3
from telethon import TelegramClient, events
from utils.extractors import extract_token

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

TELETHON_API_ID   = int(os.getenv("TELETHON_API_ID"))
TELETHON_API_HASH = os.getenv("TELETHON_API_HASH")
AWS_REGION        = os.getenv("AWS_REGION")
SQS_QUEUE_URL     = os.getenv("SQS_QUEUE_URL")


# Initializing  simple queue services and telethon client
sqs    = boto3.client('sqs', region_name=AWS_REGION)
client = TelegramClient('session', TELETHON_API_ID, TELETHON_API_HASH)

# Chats/Bots Mointoring
BOT_LIST = [
    '@cabaltrackerbot',
    '@solbixsignal',
    '@alivetrackerbot',
    '@RaydiumMCAlertBot',
    -1002450316172,
    -1002355530079,
    -1002347611734
]

@client.on(events.NewMessage(chats=BOT_LIST))
async def on_new(event):
    text = event.message.text or ""
    token_addr = extract_token(text)
    if not token_addr:
        return
    record = {
        'token_address': token_addr,
        'timestamp':     event.message.date.isoformat(),
        'bot_id':        str(event.chat_id)
    }
    
    print(f"[NEW MESSAGE] {record}")
    # Push into SQS
    response = sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(record))
    # Log SQS response metadata
    print(f"[SQS] MessageId: {response.get('MessageId')} HTTPStatus: {response.get('ResponseMetadata', {}).get('HTTPStatusCode')}")

if __name__ == '__main__':
    client.start()
    print("🔔 Collector running—listening for messages...")
    asyncio.get_event_loop().run_forever()
