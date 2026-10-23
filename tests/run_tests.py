import sys
import unittest
from datetime import datetime, timezone
from pydantic import ValidationError

from src.models.weather import WeatherObservation, WeatherForecastRequest
from src.models.financial import AssetQuote, MarketSummary
from src.pipeline import AgentDataIngestionPipeline


class TestDataIntegrityModels(unittest.TestCase):

    def test_weather_request_bounds(self):
        req = WeatherForecastRequest(city_name="Lahore", latitude=31.52, longitude=74.35)
        self.assertEqual(req.city_name, "Lahore")
        self.assertEqual(req.temperature_unit, "celsius")

        with self.assertRaises(ValidationError):
            WeatherForecastRequest(city_name="Lahore", latitude=120.0, longitude=74.35)

    def test_weather_observation_realistic_temp(self):
        obs = WeatherObservation(
            city="Lahore",
            latitude=31.52,
            longitude=74.35,
            temperature_c=28.5,
            relative_humidity=65,
            wind_speed_kmh=12.0,
            wind_direction_deg=180,
            weather_code=0,
            condition="Clear sky",
            is_day=True,
            observed_time=datetime.now(timezone.utc),
        )
        self.assertEqual(obs.temperature_c, 28.5)

        with self.assertRaises(ValidationError):
            WeatherObservation(
                city="Lahore",
                latitude=31.52,
                longitude=74.35,
                temperature_c=150.0,
                relative_humidity=65,
                wind_speed_kmh=12.0,
                wind_direction_deg=180,
                weather_code=0,
                condition="Extreme",
                is_day=True,
                observed_time=datetime.now(timezone.utc),
            )

    def test_asset_quote_ticker_and_bounds(self):
        quote = AssetQuote(
            symbol="btc",
            name="Bitcoin",
            price_usd=65000.0,
            change_24h_percent=-3.45,
            last_updated=datetime.now(timezone.utc),
        )
        self.assertEqual(quote.symbol, "BTC")

        with self.assertRaises(ValidationError):
            AssetQuote(
                symbol="BTC",
                name="Bitcoin",
                price_usd=-500.0,
                change_24h_percent=1.0,
                last_updated=datetime.now(timezone.utc),
            )

        with self.assertRaises(ValidationError):
            AssetQuote(
                symbol="BTC",
                name="Bitcoin",
                price_usd=10.0,
                change_24h_percent=-150.0,
                last_updated=datetime.now(timezone.utc),
            )

    def test_market_summary_computation(self):
        now = datetime.now(timezone.utc)
        q1 = AssetQuote(symbol="BTC", name="Bitcoin", price_usd=60000.0, change_24h_percent=2.5, market_cap_usd=1000.0, last_updated=now)
        q2 = AssetQuote(symbol="ETH", name="Ethereum", price_usd=3000.0, change_24h_percent=5.0, market_cap_usd=500.0, last_updated=now)

        summary = MarketSummary(tracked_assets=[q1, q2])
        self.assertEqual(summary.total_market_cap_usd, 1500.0)
        self.assertEqual(summary.top_performer, "ETH (+5.00%)")

    def test_untrusted_financial_batch_quarantine(self):
        pipeline = AgentDataIngestionPipeline()
        now_str = datetime.now(timezone.utc).isoformat()

        stream = [
            {"symbol": "BTC", "name": "Bitcoin", "price_usd": 68000.0, "change_24h_percent": 1.2, "last_updated": now_str},
            {"symbol": "ETH", "name": "Ethereum", "price_usd": -3000.0, "change_24h_percent": 2.0, "last_updated": now_str},
            {"symbol": "SOL#1", "name": "Solana", "price_usd": 150.0, "change_24h_percent": 0.5, "last_updated": now_str},
        ]

        report = pipeline.validate_untrusted_financial_batch(stream)
        self.assertEqual(report.total_received, 3)
        self.assertEqual(report.valid_count, 1)
        self.assertEqual(report.invalid_count, 2)
        self.assertEqual(report.status, "PARTIAL")
        self.assertEqual(len(report.quarantine_errors), 2)


if __name__ == "__main__":
    unittest.main()
