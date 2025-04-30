#!/usr/bin/env python3
import os
import requests
from solana.rpc.api import Client as SolanaClient
from dotenv import load_dotenv, find_dotenv
from dune_client.types import QueryParameter
from dune_client.client import DuneClient
from dune_client.query import QueryBase
import pandas as pd
from decimal import Decimal
# ─── Load environment variables ───────────────────────────────────────────────
dotenv_file = find_dotenv()
if not dotenv_file:
    raise RuntimeError(".env file not found in project root")
load_dotenv(dotenv_file)

# ─── Configuration ───────────────────────────────────────────────────────────
HELIUS_API_KEY_ID = os.getenv("HELIUS_API_KEY_ID")  # your Helius API key in .env
SOLANA_RPC_URL    = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
COINGECKO_BASE    = "https://api.coingecko.com/api/v3"
BASE_URL          = "https://api.helius.xyz/v0"
HELIUS_RPC_URL    = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY_ID}"
DUNE_API_KEY = os.getenv("DUNE_API_KEY")
DUNE_QUERY_ID = 5060687
dune = DuneClient(DUNE_API_KEY)


# Validate required config
if not HELIUS_API_KEY_ID:
    raise RuntimeError("Missing HELIUS_API_KEY_ID in your .env file.")

# ─── Initialize Solana RPC client ─────────────────────────────────────────────
sol_client = SolanaClient(SOLANA_RPC_URL)

# ─── Token Metadata via Helius Data API ───────────────────────────────────────
def get_token_metadata(mint: str) -> dict:
    """
    Fetch on-chain + off-chain metadata via Helius v0/token-metadata.
    Returns the first element of the JSON array result.
    """
    url = f"{BASE_URL}/token-metadata?api-key={HELIUS_API_KEY_ID}"
    payload = {"mintAccounts": [mint], "includeOffChain": True, "disableCache": False}
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data[0] if isinstance(data, list) and data else {}

# ─── Top Holders via Helius RPC getTokenLargestAccounts ──────────────────────
def get_top_holders(mint: str, limit: int = 10) -> list:
    """
    Fetch the top `limit` holders for a given token mint via Helius RPC.
    Uses getTokenLargestAccounts JSON-RPC on the Helius RPC endpoint and converts raw amounts to UI amounts by fetching decimals from metadata.
    """
    # 1) fetch decimals from metadata
    meta = get_token_metadata(mint)
    decimals = meta.get("onChainAccountInfo", {})\
                   .get("accountInfo", {})\
                   .get("data", {})\
                   .get("parsed", {})\
                   .get("info", {})\
                   .get("decimals", 0) or 0

    # 2) JSON-RPC payload to Helius RPC endpoint
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenLargestAccounts",
        "params": [mint]
    }
    resp = requests.post(HELIUS_RPC_URL, json=payload)
    resp.raise_for_status()
    values = resp.json().get("result", {}).get("value", [])[:limit]

    # 3) convert to UI amounts
    holders = []
    for v in values:
        addr = v.get("address")
        raw  = int(v.get("amount", 0))
        ui   = Decimal(str(raw / (10 ** decimals))) if decimals else Decimal(str(raw))
        holders.append({"address": addr, "amount": ui})
    return holders


import os, time, requests

DUNE_API_KEY   = os.getenv("DUNE_API_KEY")
DUNE_QUERY_ID  = 5060687
DUNE_GRAPHQL   = "https://api.dune.com/v1/graphql"

def get_dune_market_data(mint: str) -> dict:
    """
    Run your Dune query with the given token_address parameter
    and return the most recent row as a dict.
    """
    query = QueryBase(
        query_id=DUNE_QUERY_ID,
        params=[
            QueryParameter.text_type(name="token_address", value=mint),
        ],
    )
    # returns a pandas.DataFrame
    df = dune.run_query_dataframe(query)
    if df.empty:
        return {}
    # get last row
    return df.iloc[-1].to_dict()