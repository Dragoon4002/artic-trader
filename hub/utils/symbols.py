"""Symbol normalization — maps common names/tickers to canonical trading pairs."""

_SYMBOL_MAP: dict[str, str] = {
    # Bitcoin
    "BTC": "BTCUSDT",
    "BITCOIN": "BTCUSDT",
    "XBT": "BTCUSDT",
    # Ethereum
    "ETH": "ETHUSDT",
    "ETHEREUM": "ETHUSDT",
    "ETHER": "ETHUSDT",
    # Solana
    "SOL": "SOLUSDT",
    "SOLANA": "SOLUSDT",
    # BNB
    "BNB": "BNBUSDT",
    "BINANCECOIN": "BNBUSDT",
    # XRP
    "XRP": "XRPUSDT",
    "RIPPLE": "XRPUSDT",
    # Cardano
    "ADA": "ADAUSDT",
    "CARDANO": "ADAUSDT",
    # Dogecoin
    "DOGE": "DOGEUSDT",
    "DOGECOIN": "DOGEUSDT",
    # Polygon
    "MATIC": "MATICUSDT",
    "POL": "POLUSDT",
    "POLYGON": "MATICUSDT",
    # Avalanche
    "AVAX": "AVAXUSDT",
    "AVALANCHE": "AVAXUSDT",
    # Chainlink
    "LINK": "LINKUSDT",
    "CHAINLINK": "LINKUSDT",
    # Polkadot
    "DOT": "DOTUSDT",
    "POLKADOT": "DOTUSDT",
    # Litecoin
    "LTC": "LTCUSDT",
    "LITECOIN": "LTCUSDT",
    # Uniswap
    "UNI": "UNIUSDT",
    "UNISWAP": "UNIUSDT",
    # Cosmos
    "ATOM": "ATOMUSDT",
    "COSMOS": "ATOMUSDT",
    # Near
    "NEAR": "NEARUSDT",
    # Arbitrum
    "ARB": "ARBUSDT",
    "ARBITRUM": "ARBUSDT",
    # Optimism
    "OP": "OPUSDT",
    "OPTIMISM": "OPUSDT",
    # Sui
    "SUI": "SUIUSDT",
    # Aptos
    "APT": "APTUSDT",
    "APTOS": "APTUSDT",
    # Pepe
    "PEPE": "PEPEUSDT",
    # Render
    "RNDR": "RNDRUSDT",
    "RENDER": "RNDRUSDT",
    # Injective
    "INJ": "INJUSDT",
    "INJECTIVE": "INJUSDT",
    # Toncoin
    "TON": "TONUSDT",
    "TONCOIN": "TONUSDT",
}


def normalize_symbol(raw: str) -> str:
    """Normalize user input to canonical USDT pair.

    Tries the map first, then returns uppercased input if already looks like a pair.
    """
    key = raw.strip().upper()
    if key in _SYMBOL_MAP:
        return _SYMBOL_MAP[key]
    # Already a valid-looking pair (e.g. BTCUSDT, ETH/USDT)
    return key.replace("/", "")
