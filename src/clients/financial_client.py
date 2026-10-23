from datetime import datetime, timezone
from typing import Dict, List
from .http_client import ResilientHTTPClient
from ..models.financial import AssetQuote, MarketSummary

COINGECKO_MAP: Dict[str, Dict[str, str]] = {
    "bitcoin": {"symbol": "BTC", "name": "Bitcoin"},
    "ethereum": {"symbol": "ETH", "name": "Ethereum"},
    "solana": {"symbol": "SOL", "name": "Solana"},
}


class FinancialMarketClient:
    """Fetches live cryptocurrency and market rates with Pydantic V2 validation."""

    COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

    def __init__(self, http_client: ResilientHTTPClient = None):
        self.http = http_client or ResilientHTTPClient()

    async def get_market_quotes(self, coin_ids: List[str] = None) -> MarketSummary:
        """Queries CoinGecko API and returns validated MarketSummary."""
        if coin_ids is None:
            coin_ids = ["bitcoin", "ethereum", "solana"]

        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd",
            "include_market_cap": "true",
            "include_24hr_change": "true",
        }

        raw = await self.http.get_json(self.COINGECKO_URL, params=params)
        now_utc = datetime.now(timezone.utc)
        quotes: List[AssetQuote] = []

        for cid, data in raw.items():
            meta = COINGECKO_MAP.get(cid, {"symbol": cid.upper()[:4], "name": cid.capitalize()})
            quote = AssetQuote(
                symbol=meta["symbol"],
                name=meta["name"],
                price_usd=float(data.get("usd", 0.0)),
                change_24h_percent=float(data.get("usd_24h_change", 0.0)),
                market_cap_usd=float(data.get("usd_market_cap", 0.0)) if "usd_market_cap" in data else None,
                last_updated=now_utc,
            )
            quotes.append(quote)

        summary = MarketSummary(tracked_assets=quotes)
        return summary
