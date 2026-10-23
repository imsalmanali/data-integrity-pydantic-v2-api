import logging
from typing import Any, Dict, List
from pydantic import ValidationError
from .models.agent_payload import AgentToolPayload, DataIntegrityReport
from .models.weather import WeatherObservation
from .models.financial import AssetQuote, MarketSummary
from .clients.weather_client import WeatherClient
from .clients.financial_client import FinancialMarketClient

logger = logging.getLogger("agentic.pipeline")


class AgentDataIngestionPipeline:
    """
    Core Ingestion Engine for Agentic AI Systems.
    Enforces a strict quarantine boundary: untrusted external data must pass
    Pydantic V2 schema validation before being injected into an Agent's memory or LLM context.
    """

    def __init__(self, weather_client: WeatherClient = None, financial_client: FinancialMarketClient = None):
        self.weather_client = weather_client or WeatherClient()
        self.financial_client = financial_client or FinancialMarketClient()

    async def fetch_weather_for_agent(self, city: str, lat: float, lon: float) -> AgentToolPayload:
        """Fetch live meteorological data, validate, and build agent context payload."""
        source = f"{WeatherClient.OPEN_METEO_URL}?lat={lat}&lon={lon}"
        try:
            obs: WeatherObservation = await self.weather_client.get_current_weather(city, lat, lon)
            audit = DataIntegrityReport(
                total_received=1,
                valid_count=1,
                invalid_count=0,
                status="SUCCESS",
            )
            summary = (
                f"Current weather in {obs.city}: {obs.temperature_c}°C ({obs.condition}), "
                f"Humidity: {obs.relative_humidity}%, Wind: {obs.wind_speed_kmh} km/h."
            )
            return AgentToolPayload(
                tool_name="get_current_weather",
                source_url=source,
                status="SUCCESS",
                data=obs.model_dump(mode="json"),
                audit=audit,
                agent_summary=summary,
            )
        except Exception as exc:
            logger.error(f"Weather pipeline error: {exc}")
            audit = DataIntegrityReport(
                total_received=1,
                valid_count=0,
                invalid_count=1,
                quarantine_errors=[{"error": str(exc)}],
                status="FAILED",
            )
            return AgentToolPayload(
                tool_name="get_current_weather",
                source_url=source,
                status="ERROR",
                data={},
                audit=audit,
                agent_summary=f"Failed to fetch verified weather data for {city}: {exc}",
            )

    async def fetch_financial_summary_for_agent(self) -> AgentToolPayload:
        """Fetch live crypto market quotes, validate, and assemble financial summary."""
        source = FinancialMarketClient.COINGECKO_URL
        try:
            summary: MarketSummary = await self.financial_client.get_market_quotes()
            audit = DataIntegrityReport(
                total_received=len(summary.tracked_assets),
                valid_count=len(summary.tracked_assets),
                invalid_count=0,
                status="SUCCESS",
            )
            quotes_str = ", ".join([f"{a.symbol}: ${a.price_usd:,.2f} ({a.change_24h_percent:+.2f}%)" for a in summary.tracked_assets])
            agent_text = f"Market Status: {summary.market_status} | Assets: [{quotes_str}] | Top Performer: {summary.top_performer}"

            return AgentToolPayload(
                tool_name="get_market_summary",
                source_url=source,
                status="SUCCESS",
                data=summary.model_dump(mode="json"),
                audit=audit,
                agent_summary=agent_text,
            )
        except Exception as exc:
            logger.error(f"Financial pipeline error: {exc}")
            audit = DataIntegrityReport(
                total_received=0,
                valid_count=0,
                invalid_count=1,
                quarantine_errors=[{"error": str(exc)}],
                status="FAILED",
            )
            return AgentToolPayload(
                tool_name="get_market_summary",
                source_url=source,
                status="ERROR",
                data={},
                audit=audit,
                agent_summary=f"Failed to fetch market data: {exc}",
            )

    def validate_untrusted_financial_batch(self, raw_records: List[Dict[str, Any]]) -> DataIntegrityReport:
        """
        Simulates parsing a dirty webhook or untrusted third-party batch.
        Catches corrupted fields, negative values, and schema violations.
        """
        valid_records: List[AssetQuote] = []
        quarantine_errors: List[Dict[str, Any]] = []

        for idx, item in enumerate(raw_records):
            try:
                quote = AssetQuote.model_validate(item)
                valid_records.append(quote)
            except ValidationError as err:
                quarantine_errors.append({
                    "record_index": idx,
                    "rejected_payload": item,
                    "validation_errors": err.errors(include_url=False),
                })

        total = len(raw_records)
        valid = len(valid_records)
        invalid = len(quarantine_errors)

        status = "SUCCESS" if invalid == 0 else ("PARTIAL" if valid > 0 else "FAILED")

        return DataIntegrityReport(
            total_received=total,
            valid_count=valid,
            invalid_count=invalid,
            quarantine_errors=quarantine_errors,
            status=status,
        )
