from dataclasses import dataclass
from datetime import datetime


@dataclass
class Metric:
    id: str
    request_timestamp: datetime
    response_time: int
    status_code: int
    page_content: str | None
