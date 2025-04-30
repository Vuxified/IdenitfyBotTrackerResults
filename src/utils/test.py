#!/usr/bin/env python3
import json
from utils.api_clients import (
    get_token_metadata,
    get_top_holders,
    get_dune_market_data
)

def main():
    mint = input("Enter a Solana token mint address: ").strip() \
        or "6Aubp6pD3LqsZCxLVJAWP7gy5P1eML3hubuhPnWjpump"

    # 1) Metadata
    print("\n🔍 Token Metadata:")
    try:
        meta = get_token_metadata(mint)
        print(json.dumps(meta, indent=2))
    except Exception as e:
        print(f"[ERROR] Metadata: {e}")

    # 2) Top Holders
    print("\n🔍 Top 5 Holders:")
    try:
        holders = get_top_holders(mint, limit=5)
        print(json.dumps(holders, indent=2))
    except Exception as e:
        print(f"[ERROR] Top holders: {e}")

    # 3) Dune Market Data
    print("\n🔍 Market Data (Dune):")
    try:
        market = get_dune_market_data(mint)
        print(json.dumps(market, indent=2))
    except Exception as e:
        print(f"[ERROR] Market data (Dune): {e}")

if __name__ == "__main__":
    main()
