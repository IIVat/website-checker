from dataclasses import dataclass


@dataclass
class UrlData:
    id: int
    url: str
    content_regex: str | None
