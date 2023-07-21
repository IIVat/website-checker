from app.database.database import Database
from app.model.metric import Metric
from app.model.url import UrlData

import dataclasses


class MetricsRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def get_urls(self) -> list[UrlData]:
        table_name = "websites_urls"
        query = f"SELECT * FROM {table_name}"
        rows = self.database.get_rows(query)
        return [UrlData(row[0], row[1], row[2]) for row in rows]

    def save_metrics(self, batch: list[Metric]) -> None:
        metrics = [dataclasses.asdict(metric) for metric in batch]
        query = """
                INSERT INTO websites_metrics (url_id, request_timestamp, response_time, status_code, page_content)
                VALUES (%(id)s, %(request_timestamp)s, %(response_time)s, %(status_code)s, %(page_content)s)
                ON CONFLICT (url_id)
                DO UPDATE SET
                    request_timestamp = EXCLUDED.request_timestamp,
                    response_time = EXCLUDED.response_time,
                    status_code = EXCLUDED.status_code,
                    page_content = EXCLUDED.page_content;
                """
        self.database.execute_batch(query, metrics)
