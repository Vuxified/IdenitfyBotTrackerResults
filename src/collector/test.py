import sys
print("▶ Running with Python:", sys.executable)

import boto3
print("▶ boto3 loaded from:", boto3.__file__)

# (then your existing imports...)
from telethon import TelegramClient, events
# …
