#!/usr/bin/env python3
import os
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import boto3
import requests
from decimal import Decimal


# ─── Import our helpers after adjusting path ─────────────────────────────────
from utils.extractors import extract_token
from utils.api_clients import (
    get_token_metadata,
    get_top_holders,
    get_dune_market_data
)

# ─── Load environment variables ───────────────────────────────────────────────
dotenv_file = find_dotenv()
if not dotenv_file:
    raise RuntimeError(".env file not found in project root")
load_dotenv(dotenv_file)

AWS_REGION     = os.getenv("AWS_REGION")
SQS_QUEUE_URL  = os.getenv("SQS_QUEUE_URL")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

# Validate required config
missing = [k for k in ("AWS_REGION","SQS_QUEUE_URL","DYNAMODB_TABLE","HELIUS_API_KEY") if not os.getenv(k)]
if missing:
    raise RuntimeError(f"Missing config vars: {', '.join(missing)}")

# ─── AWS clients ─────────────────────────────────────────────────────────────
sqs = boto3.client("sqs", region_name=AWS_REGION)
ddb = boto3.resource("dynamodb", region_name=AWS_REGION).Table(DYNAMODB_TABLE)

# ─── Helper to retry on 429, skip on 400 ─────────────────────────────────────
def safe_call(fn, *args, **kwargs):
    """
    Call fn(*args), retry once on 429 (rate limit), return None on 400 (bad mint),
    raise for other errors.
    """
    for attempt in range(2):
        try:
            result = fn(*args, **kwargs)
            return result
        except requests.HTTPError as e:
            code = e.response.status_code
            if code == 400:
                # invalid mint, skip further processing
                return None
            if code == 429 and attempt == 0:
                # rate limit: back off and retry once
                time.sleep(1)
                continue
            # other HTTP errors or second rate-limit attempt: raise
            raise
    return None
def convert_floats(obj):
    if isinstance(obj, list):
        return [convert_floats(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_floats(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj

# ─── Main poll loop ──────────────────────────────────────────────────────────
def poll_loop():
    while True:
        resp = sqs.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=20
        )
        messages = resp.get("Messages", [])
        for msg in messages:
            body = msg.get("Body", "")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                print(f"[ERROR] Invalid JSON: {body}")
                sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=msg['ReceiptHandle'])
                continue

            raw = data.get("token_address", "")
            mint = extract_token(raw)
            if not mint:
                print(f"[SKIP] No valid Solana mint in: {raw}")
                sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=msg['ReceiptHandle'])
                continue

            # Enrich via Helius + CoinGecko with safe_call
            try:
                metadata  = safe_call(get_token_metadata, mint)
                if metadata is None:
                    print(f"[BAD MINT] {mint}")
                    sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=msg['ReceiptHandle'])
                    continue

                holders   = safe_call(get_top_holders, mint)
                market    = safe_call(get_dune_market_data, mint)

                # Combine and write
                item = convert_floats({
                **data,
                "token_address": mint,
                "metadata":      metadata,
                "top_holders":   holders   or [],
                "market_data":   market    or {}
                })


                ddb.put_item(Item=item)
                print(f"[ENRICHED] {mint}")
                sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=msg['ReceiptHandle'])
            except Exception as e:
                print(f"[ERROR] processing mint {mint}: {e}")

        # avoid tight loop
        time.sleep(0.5)

if __name__ == '__main__':
    print(f"▶ Python: {sys.executable}")
    print("🚀 Enricher worker starting…")
    poll_loop()
