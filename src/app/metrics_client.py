from . import logger
from aiohttp import ClientSession
from app.model.metric import Metric
from app.model.url import UrlData
from datetime import datetime

import aiohttp
import asyncio


class MetricsClient:
    def __init__(self) -> None:
        pass

    # Function to check website availability and collect metrics
    async def get_metric(self, url_data: UrlData):
        logger.info(f"Checking liveness of {url_data.url}")
        try:
            # This is poor approach to create a session for each request.
            session = ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False))
            async with session:
                async with session.get(url_data.url) as response:
                    start_time = datetime.utcnow()
                    await response.read()
                    status_code = response.status
                    end_time = datetime.utcnow()
                    latency = (end_time - start_time).total_seconds()
                    response_time = round(latency * 1000)
                    logger.info(
                        f"""Received the metrics for {url_data.url}:
                        status_code={status_code},
                        start_time={start_time},
                        response_time={response_time}ms"""
                    )
                    return Metric(url_data.id, start_time, response_time, status_code, None)
        except aiohttp.ClientError as e:
            logger.error(f"Request for url: {url_data.url} failed: {e}")
            return None


if __name__ == "__main__":
    c = MetricsClient().get_metric(UrlData(1, "https://www.google.com", None))
    asyncio.run(c)
