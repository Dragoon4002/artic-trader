"""
Pyth Network price client — fetches live prices from Hermes REST API.
No API key needed (Hermes is public).
"""
import time
from typing import Dict, List, Optional

import requests

HERMES_URL = "https://hermes.pyth.network"

# Verified feed IDs from hermes.pyth.network/v2/price_feeds (Apr 2026)
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

SYMBOL_ALIASES: Dict[str, str] = {
    "MATIC": "POL",
}

# Reverse map: feed_id (no 0x) → base symbol
_ID_TO_SYMBOL: Dict[str, str] = {
    v.replace("0x", ""): k for k, v in PYTH_FEED_IDS.items()
}


def _normalize_base(symbol: str) -> str:
    """BTCUSDT / BINANCE:ETHUSDT / BTC/USD → BTC"""
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


def _parse_price(price_info: dict) -> float:
    """Parse Hermes price object → float."""
    return int(price_info["price"]) * (10 ** price_info["expo"])


def _parse_conf(price_info: dict) -> float:
    """Parse Hermes confidence → float."""
    return int(price_info["conf"]) * (10 ** price_info["expo"])


class PythClient:
    def __init__(self, timeout: int = 10):
        self._timeout = timeout

    def _feed_id(self, symbol: str) -> Optional[str]:
        base = _normalize_base(symbol)
        return PYTH_FEED_IDS.get(base)

    def is_supported(self, symbol: str) -> bool:
        return self._feed_id(symbol) is not None

    def get_price(self, symbol: str) -> Optional[float]:
        feed_id = self._feed_id(symbol)
        if not feed_id:
            return None
        try:
            r = requests.get(
                f"{HERMES_URL}/v2/updates/price/latest",
                params={"ids[]": feed_id},
                timeout=self._timeout,
            )
            r.raise_for_status()
            parsed = r.json().get("parsed", [])
            if parsed:
                return _parse_price(parsed[0]["price"])
        except Exception as e:
            print(f"[PYTH] price fetch failed for {symbol}: {e}")
        return None

    def get_price_with_retry(self, symbol: str, max_retries: int = 3) -> Optional[float]:
        for attempt in range(max_retries):
            price = self.get_price(symbol)
            if price is not None:
                return price
            if attempt < max_retries - 1:
                time.sleep(0.3)
        return None

    def get_price_with_confidence(self, symbol: str) -> Optional[dict]:
        feed_id = self._feed_id(symbol)
        if not feed_id:
            return None
        try:
            r = requests.get(
                f"{HERMES_URL}/v2/updates/price/latest",
                params={"ids[]": feed_id},
                timeout=self._timeout,
            )
            r.raise_for_status()
            parsed = r.json().get("parsed", [])
            if parsed:
                pi = parsed[0]["price"]
                return {
                    "price": _parse_price(pi),
                    "conf": _parse_conf(pi),
                    "publish_time": pi.get("publish_time"),
                }
        except Exception as e:
            print(f"[PYTH] confidence fetch failed for {symbol}: {e}")
        return None

    def get_prices_batch(self, symbols: List[str]) -> Dict[str, float]:
        ids = []
        base_for_id = {}
        for sym in symbols:
            fid = self._feed_id(sym)
            if fid:
                ids.append(fid)
                base_for_id[fid.replace("0x", "")] = _normalize_base(sym)
        if not ids:
            return {}
        try:
            r = requests.get(
                f"{HERMES_URL}/v2/updates/price/latest",
                params=[("ids[]", fid) for fid in ids],
                timeout=self._timeout,
            )
            r.raise_for_status()
            out: Dict[str, float] = {}
            for p in r.json().get("parsed", []):
                base = base_for_id.get(p.get("id", ""))
                if base:
                    out[base] = _parse_price(p["price"])
            return out
        except Exception as e:
            print(f"[PYTH] batch fetch failed: {e}")
        return {}
