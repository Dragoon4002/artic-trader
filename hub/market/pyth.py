"""Async batch price fetcher using Pyth Hermes REST API."""

import logging
from datetime import datetime, timezone
from typing import Dict

import httpx

logger = logging.getLogger(__name__)

HERMES_URL = "https://hermes.pyth.network"

# Feed IDs — same as app/market/pyth_client.py
PYTH_FEED_IDS: Dict[str, str] = {
    "BTC": "0xe62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43",
    "ETH": "0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace",
    "BNB": "0x2f95862b045670cd22bee3114c39763a4a08beeb663b145d283c31d7d1101c4f",
    "SOL": "0xef0d8b6fda2ceba41da15d4095d1da392a0d2f8ed0c6c7bc0f4cfac8c280b56d",
    "XRP": "0xec5d399846a9209f3fe5881d70aae9268c94339ff9817e8d18ff19fa05eea1c8",
    "ADA": "0x2a01deaec9e51a579277b34b122399984d0bbf57e2458a7e42fecd2829867a0d",
    "DOGE": "0xdcef50dd0a4cd2dcc17e45df1676dcb336a11a61c69df7a0299b0150c672d25c",
    "AVAX": "0x93da3352f9f1d105fdfe4971cfa80e9dd777bfc5d0f683ebb6e1294b92137bb7",
    "DOT": "0xca3eed9b267293f6595901c734c7525ce8ef49adafe8284606ceb307afa2ca5b",
    "LINK": "0x8ac0c70fff57e9aefdf5edf44b51d62c2d433653cbb2cf5cc06bb115af04d221",
    "UNI": "0x78d185a741d07edb3412b09008b7c5cfb9bbbd7d568bf00ba737b456ba171501",
    "ATOM": "0xb00b60f88b03a6a625a8d1c048c3f66653edf217439983d037e7222c4e612819",
    "LTC": "0x6e3f3fa8253588df9326580180233eb791e03b443a3ba7a1d892e73874e19a54",
    "NEAR": "0xc415de8d2eba7db216527dff4b60e8f3a5311c740dadb233e13e12547e226750",
    "APT": "0x03ae4db29ed4ae33d323568895aa00337e658e348b37509f5372ae51f0af00d5",
    "ARB": "0x3fa4252848f9f0a1480be62745a4629d9eb1322aebab8a791e344b3b9c1adcf5",
    "OP": "0x385f64d993f7b77d8182ed5003d97c60aa3361f3cecfe711544d2d59165e9bdf",
    "SUI": "0x23d7315113f5b1d3ba7a83604c44b94d79f4fd69af77f804fc7f920a6dc65744",
    "INJ": "0x7a5bc1d2b56ad029048cd63964b3ad2776eadf812edc1a43a31406cb54bff592",
    "AAVE": "0x2b9ab1e972a281585084148ba1389800799bd4be63b957507db1349314e47445",
    "FIL": "0x150ac9b959aee0051e4091f0ef5216d941f590e1c5e7f91cf7635b5c11628c0e",
    "PEPE": "0xd69731a2e74ac1ce884fc3890f7ee324b6deb66147055249568869ed700882e4",
    "POL": "0xffd11c5a1cfd42f80afb2df4d9f264c15f956d68153335374ec10722edd70472",
    "BCH": "0x3dd2b63686a450ec7290df3a1e0b583c0481f651351edfa7636f39aed55cf8a3",
    "ETC": "0x7f5cc8d963fc5b3d2ae41fe5685ada89fd4f14b435f8050f28c7fd409f40c2d8",
    "XLM": "0xb7a8eba68a997cd0210c2e1e4ee811ad2d174b3611c22d9ebf16f4cb7e9ba850",
    "HBAR": "0x3728e591097635310e6341af53db8b7ee42da9b3a8d918f9463ce9cca886dfbd",
}

SYMBOL_ALIASES: Dict[str, str] = {"MATIC": "POL"}

_ID_TO_SYMBOL: Dict[str, str] = {
    v.replace("0x", ""): k for k, v in PYTH_FEED_IDS.items()
}


def normalize_base(symbol: str) -> str:
    """BTCUSDT / BTC/USD / BINANCE:ETHUSDT → BTC"""
    s = symbol.strip().upper()
    if ":" in s:
        s = s.split(":")[-1]
    if "/" in s:
        s = s.split("/")[0]
    for suffix in ("USDT", "USD", "BUSD", "USDC", "PERP"):
        if s.endswith(suffix) and len(s) > len(suffix):
            s = s[: -len(suffix)]
            break
    return SYMBOL_ALIASES.get(s, s)


async def fetch_prices_batch(symbols: list[str]) -> dict[str, dict]:
    """Batch fetch prices from Pyth Hermes. Returns {original_symbol: {price, fetched_at}}."""
    if not symbols:
        return {}

    # Dedupe and map to feed IDs
    feed_map: dict[str, str] = {}  # feed_id -> original_symbol
    for sym in symbols:
        base = normalize_base(sym)
        fid = PYTH_FEED_IDS.get(base)
        if fid:
            feed_map[fid] = sym

    if not feed_map:
        logger.warning(f"[PythProxy] No feed IDs for: {symbols}")
        return {}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(
                f"{HERMES_URL}/v2/updates/price/latest",
                params=[("ids[]", fid) for fid in feed_map],
            )
            r.raise_for_status()
            data = r.json()

        now = datetime.now(timezone.utc).isoformat()
        prices: dict[str, dict] = {}
        for item in data.get("parsed", []):
            raw_id = "0x" + item["id"]
            if raw_id in feed_map:
                pi = item["price"]
                price = int(pi["price"]) * (10 ** pi["expo"])
                sym = feed_map[raw_id]
                prices[sym] = {"symbol": sym, "price": price, "fetched_at": now}

        return prices
    except Exception as e:
        logger.error(f"[PythProxy] Batch fetch failed: {e}")
        return {}
