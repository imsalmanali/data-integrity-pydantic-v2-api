import asyncio
import logging
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger("agentic.http")


class ResilientHTTPClient:
    """
    Production-grade asynchronous HTTP client with timeout,
    retry backoff, and exception containment.
    """

    def __init__(self, timeout: float = 10.0, max_retries: int = 3, backoff_factor: float = 0.5):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.headers = {
            "User-Agent": "AgenticAI-DataIntegrityPipeline/1.0 (Salman Ali; https://github.com/imsalmanali)",
            "Accept": "application/json",
        }

    async def get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes an asynchronous GET request with exponential retry backoff.
        Raises RuntimeError on persistent failures.
        """
        attempt = 0
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            while attempt < self.max_retries:
                attempt += 1
                try:
                    logger.info(f"GET {url} (Attempt {attempt}/{self.max_retries})")
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()
                except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                    logger.warning(f"HTTP attempt {attempt} failed for {url}: {exc}")
                    if attempt >= self.max_retries:
                        raise RuntimeError(
                            f"HTTP request exhausted {self.max_retries} retries for URL {url}: {exc}"
                        ) from exc
                    await asyncio.sleep(self.backoff_factor * (2 ** (attempt - 1)))
        raise RuntimeError(f"Unexpected exit while requesting {url}")
