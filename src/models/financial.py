from datetime import datetime, timezone
from typing import List, Optional
from pydantic import ConfigDict, Field, field_validator, model_validator
from .base import TimestampedModel


class AssetQuote(TimestampedModel):
    """
    Validated real-time financial market price.
    Critical for financial intelligence and automated decision agents.
    """
    symbol: str = Field(..., min_length=2, max_length=15, description="Asset ticker symbol, e.g. BTC, ETH")
    name: str = Field(..., min_length=1, description="Full descriptive name")
    price_usd: float = Field(..., gt=0.0, description="Current price in USD, strictly positive")
    change_24h_percent: float = Field(..., description="24-hour percentage price change")
    volume_24h_usd: Optional[float] = Field(default=None, ge=0.0, description="24-hour trading volume in USD")
    market_cap_usd: Optional[float] = Field(default=None, ge=0.0, description="Total market capitalization")
    last_updated: datetime = Field(..., description="Timestamp of the market data source")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned.isalnum():
            raise ValueError(f"Ticker symbol '{v}' must be alphanumeric.")
        return cleaned

    @field_validator("change_24h_percent")
    @classmethod
    def validate_change_bounds(cls, v: float) -> float:
        # Protect against anomalous API corruptions (e.g. integer overflow)
        if v < -100.0:
            raise ValueError(f"Price change cannot drop below -100% (got {v}%).")
        return round(v, 4)

    @model_validator(mode="after")
    def verify_recency(self) -> "AssetQuote":
        # Disallow data timestamped more than 7 days into the future (clock skew guard)
        now = datetime.now(timezone.utc)
        if self.last_updated.tzinfo is None:
            updated_utc = self.last_updated.replace(tzinfo=timezone.utc)
        else:
            updated_utc = self.last_updated

        delta = (updated_utc - now).total_seconds()
        if delta > 3600 * 24:
            raise ValueError(f"Market update timestamp is suspiciously in the future: {self.last_updated}")
        return self


class MarketSummary(TimestampedModel):
    """Aggregated market intelligence for agent consumption."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, validate_assignment=False)

    market_status: str = Field(default="OPEN", description="Market status")
    tracked_assets: List[AssetQuote] = Field(default_factory=list, description="List of validated quotes")
    total_market_cap_usd: float = Field(default=0.0, ge=0.0)
    top_performer: Optional[str] = None

    @model_validator(mode="after")
    def compute_summary_metrics(self) -> "MarketSummary":
        if self.tracked_assets:
            total_cap = sum(a.market_cap_usd for a in self.tracked_assets if a.market_cap_usd)
            self.total_market_cap_usd = round(total_cap, 2)
            top = max(self.tracked_assets, key=lambda a: a.change_24h_percent)
            self.top_performer = f"{top.symbol} ({top.change_24h_percent:+.2f}%)"
        return self
