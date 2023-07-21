from . import logger
from app.database.database import PostgreSqlDatabase
from app.database.repository import MetricsRepository
from app.metrics_client import MetricsClient
from app.model.metric import Metric
from app.model.url import UrlData
from config.settings import DATABASE_URL
from reactivex.scheduler.eventloop import AsyncIOThreadSafeScheduler
from reactivex.subject import Subject


import asyncio
import reactivex
import reactivex.operators as ops


class WebsiteChecker:
    def __init__(
        self,
        client: MetricsClient,
        repository: MetricsRepository,
        polling_interval: float,
        time_window: float,
        batch_size: int,
    ):
        self.client = client
        self.repository = repository
        self.metrics_subject = Subject()
        self.polling_interval = polling_interval
        self.time_window = time_window
        self.batch_size = batch_size

    def check_liveness(self):
        """Calls websites, receives results and put it in observer"""
        loop = asyncio.get_event_loop()
        scheduler = AsyncIOThreadSafeScheduler(loop)
        logger.info("Starting to check websites' livness: ")
        return (
            reactivex.interval(self.polling_interval)
            .pipe(
                ops.start_with(0),  # To trigger the first check immediately
                ops.flat_map(lambda _: self.__source()),
                ops.map(lambda data: loop.create_task(self.__call_website(data))),
                ops.merge_all(),
            )
            .subscribe(
                on_next=lambda metric: self.metrics_subject.on_next(metric),
                on_error=lambda err: logger.error(f"Error was raised: {err}"),
                scheduler=scheduler,
            )
        )

    def collect_metrics(self):
        """Buffers the collected metrics within a time window and send the batch to the database
        Groups metrics within a time window or by batch size
        Only sends non-empty batches
        """
        logger.info("Collecting websites metrics: ")
        loop = asyncio.get_event_loop()
        scheduler = AsyncIOThreadSafeScheduler(loop)
        return self.metrics_subject.pipe(
            ops.buffer_with_time_or_count(self.time_window, self.batch_size),
            ops.filter(lambda metrics_batch: len(metrics_batch) > 0),
            ops.map(lambda metrics_batch: self.__insert_metrics_batch(metrics_batch)),
        ).subscribe(
            lambda value: logger.info(f"Published {value} elems"),
            on_error=lambda err: logger.error(f"Error was raised: {err}"),
            scheduler=scheduler,
        )

    async def __call_website(self, url_data: UrlData):
        """Function to check website availability and collect metrics"""
        metric = await self.client.get_metric(url_data)
        if metric is not None:
            return metric

    def __insert_metrics_batch(self, metrics_batch: list[Metric]):
        self.repository.save_metrics(metrics_batch)
        return len(metrics_batch)

    def __source(self):
        """The method fetches all urls from db.
        Of course the approach is poor, especially if we have a huge amount of records in db.
        But this can be discussed.
        """
        logger.info("Getting source from database: ")
        source = reactivex.from_iterable(self.repository.get_urls())
        source.subscribe(lambda v: logger.info(f"Fetched from db: {v}"))
        return source


# Example
if __name__ == "__main__":
    pg_db = PostgreSqlDatabase(dsn=DATABASE_URL)
    repo = MetricsRepository(database=pg_db)
    metrics_client = MetricsClient()
    web_checker = WebsiteChecker(client=metrics_client, repository=repo)
    asyncio.run(web_checker.__call_website(UrlData(1, "https://google.com", None)))
