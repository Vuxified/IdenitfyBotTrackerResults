import re

# Solana addresses are base58 encoded and typically 32-44 characters
SOL_PATTERN = re.compile(r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b')

def extract_token(text: str) -> str:
    """Return the first Solana-style address found in text, or empty string."""
    match = SOL_PATTERN.search(text)
    return match.group(0) if match else ""
