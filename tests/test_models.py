import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from src.models.weather import WeatherObservation, WeatherForecastRequest
from src.models.financial import AssetQuote, MarketSummary


def test_weather_request_bounds():
    req = WeatherForecastRequest(city_name="Lahore", latitude=31.52, longitude=74.35)
    assert req.city_name == "Lahore"
    assert req.temperature_unit == "celsius"

    with pytest.raises(ValidationError):
        WeatherForecastRequest(city_name="Lahore", latitude=120.0, longitude=74.35)


def test_weather_observation_realistic_temp():
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
    assert obs.temperature_c == 28.5

    # Out of earth range temperature must raise ValidationError
    with pytest.raises(ValidationError):
        WeatherObservation(
            city="Lahore",
            latitude=31.52,
            longitude=74.35,
            temperature_c=150.0,  # Corrupted sensor
            relative_humidity=65,
            wind_speed_kmh=12.0,
            wind_direction_deg=180,
            weather_code=0,
            condition="Extreme",
            is_day=True,
            observed_time=datetime.now(timezone.utc),
        )


def test_asset_quote_ticker_and_bounds():
    quote = AssetQuote(
        symbol="btc",
        name="Bitcoin",
        price_usd=65000.0,
        change_24h_percent=-3.45,
        last_updated=datetime.now(timezone.utc),
    )
    assert quote.symbol == "BTC"  # Normalized to uppercase

    # Rejection of negative price
    with pytest.raises(ValidationError):
        AssetQuote(
            symbol="BTC",
            name="Bitcoin",
            price_usd=-500.0,
            change_24h_percent=1.0,
            last_updated=datetime.now(timezone.utc),
        )

    # Rejection of drop below -100%
    with pytest.raises(ValidationError):
        AssetQuote(
            symbol="BTC",
            name="Bitcoin",
            price_usd=10.0,
            change_24h_percent=-150.0,
            last_updated=datetime.now(timezone.utc),
        )


def test_market_summary_computation():
    now = datetime.now(timezone.utc)
    q1 = AssetQuote(symbol="BTC", name="Bitcoin", price_usd=60000.0, change_24h_percent=2.5, market_cap_usd=1000.0, last_updated=now)
    q2 = AssetQuote(symbol="ETH", name="Ethereum", price_usd=3000.0, change_24h_percent=5.0, market_cap_usd=500.0, last_updated=now)

    summary = MarketSummary(tracked_assets=[q1, q2])
    assert summary.total_market_cap_usd == 1500.0
    assert summary.top_performer == "ETH (+5.00%)"
