import asyncio
import json
import logging
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.pipeline import AgentDataIngestionPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


async def main():
    print("=" * 75)
    print("🚀 AGENTIC AI CAREER SPRINT | MILESTONE 1")
    print("📌 Topic: Data Integrity, Pydantic V2 & Resilient HTTP APIs")
    print("👤 Engineer: Salman Ali (https://github.com/imsalmanali)")
    print("=" * 75)
    print()

    pipeline = AgentDataIngestionPipeline()

    # 1. Real-World Live API Query: Weather
    print("🌦️ [Step 1] Ingesting Live Real-Time Weather via Open-Meteo API...")
    cities = [
        {"name": "Lahore", "lat": 31.5204, "lon": 74.3587},
        {"name": "London", "lat": 51.5074, "lon": -0.1278},
        {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
    ]

    for c in cities:
        payload = await pipeline.fetch_weather_for_agent(c["name"], c["lat"], c["lon"])
        print(f"  ✅ {c['name']}: {payload.agent_summary}")
        print(f"     [Status: {payload.status}] Ingested At: {payload.ingested_at.isoformat()}")
    print()

    # 2. Real-World Live API Query: Crypto / Financial Rates
    print("📈 [Step 2] Ingesting Live Financial Intelligence via CoinGecko API...")
    fin_payload = await pipeline.fetch_financial_summary_for_agent()
    print(f"  ✅ Market Ingestion: {fin_payload.agent_summary}")
    print()

    # 3. Untrusted Data Quarantine & Validation Defense
    print("🛡️ [Step 3] Simulating Untrusted / Corrupted Webhook Data Stream...")
    untrusted_stream = [
        # Valid Record
        {
            "symbol": "BTC",
            "name": "Bitcoin",
            "price_usd": 68500.25,
            "change_24h_percent": 2.15,
            "market_cap_usd": 1350000000000.0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        },
        # Corrupted 1: Negative Price (Financial impossibility)
        {
            "symbol": "FAKECOIN",
            "name": "Poison Token",
            "price_usd": -150.0,
            "change_24h_percent": 10.0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        },
        # Corrupted 2: Invalid Symbol characters
        {
            "symbol": "BAD$$COIN!",
            "name": "Hacked Asset",
            "price_usd": 12.50,
            "change_24h_percent": -5.0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        },
        # Corrupted 3: Impossible Drop (< -100%)
        {
            "symbol": "CRASH",
            "name": "Crash Coin",
            "price_usd": 0.05,
            "change_24h_percent": -150.0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        },
    ]

    report = pipeline.validate_untrusted_financial_batch(untrusted_stream)
    print(f"  🔍 Total Records Processed: {report.total_received}")
    print(f"  🟢 Accepted Valid Records: {report.valid_count}")
    print(f"  🔴 Quarantined / Rejected: {report.invalid_count}")
    print(f"  ⚠️ Pipeline Integrity Status: {report.status}")
    print()
    print("  📋 Quarantined Audit Trace (Sample):")
    for err in report.quarantine_errors:
        print(f"    - Index {err['record_index']} ({err['rejected_payload'].get('symbol')}):")
        for detail in err["validation_errors"]:
            print(f"        Field '{detail['loc'][0]}': {detail['msg']}")
    print()

    # 4. Agent Tool Payload Preview
    print("📦 [Step 4] Final Structured Payload Dispatched to LLM Agent:")
    sample_agent_json = json.dumps(fin_payload.model_dump(mode="json"), indent=2)
    print(sample_agent_json[:700] + "\n  ... [truncated for display]")
    print()
    print("=" * 75)
    print("✨ Pipeline executed successfully with zero data leakage!")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(main())
