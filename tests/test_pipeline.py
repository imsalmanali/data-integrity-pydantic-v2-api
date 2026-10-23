import pytest
from datetime import datetime, timezone
from src.pipeline import AgentDataIngestionPipeline


def test_untrusted_financial_batch_quarantine():
    pipeline = AgentDataIngestionPipeline()
    now_str = datetime.now(timezone.utc).isoformat()

    stream = [
        {"symbol": "BTC", "name": "Bitcoin", "price_usd": 68000.0, "change_24h_percent": 1.2, "last_updated": now_str},
        {"symbol": "ETH", "name": "Ethereum", "price_usd": -3000.0, "change_24h_percent": 2.0, "last_updated": now_str}, # Negative price
        {"symbol": "SOL#1", "name": "Solana", "price_usd": 150.0, "change_24h_percent": 0.5, "last_updated": now_str},   # Invalid symbol
    ]

    report = pipeline.validate_untrusted_financial_batch(stream)
    assert report.total_received == 3
    assert report.valid_count == 1
    assert report.invalid_count == 2
    assert report.status == "PARTIAL"
    assert len(report.quarantine_errors) == 2
