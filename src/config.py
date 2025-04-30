from dotenv import load_dotenv
import os

# loading variables
load_dotenv()

TELETHON_API_ID   = int(os.getenv("TELETHON_API_ID"))
TELETHON_API_HASH = os.getenv("TELETHON_API_HASH")
AWS_REGION        = os.getenv("AWS_REGION")
SQS_QUEUE_URL     = os.getenv("SQS_QUEUE_URL")
DYNAMODB_TABLE    = os.getenv("DYNAMODB_TABLE")

