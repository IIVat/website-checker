from app.database.database import PostgreSqlDatabase
from app.database.repository import MetricsRepository
from app.metrics_client import MetricsClient
from app.website_checker import WebsiteChecker
from config.config import Config
from config.settings import DATABASE_URL

import asyncio
import logging
import logging.config
import sys


def init_logger():
    # Create a logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Create a formatter
    log_format = "[%(asctime)s] [%(levelname)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, date_format)

    # Create a console handler and set the log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


async def main():
    logger = init_logger()

    logger.info("Initializing application...")

    config = Config()

    logger.info(
        f"""Configuration:
                            polling_interval={config.polling_interval},
                            time_window={config.time_window},
                            batch_size={config.time_window}"""
    )

    logger.info("Initializing database...")

    pg_db = PostgreSqlDatabase(dsn=DATABASE_URL)
    repo = MetricsRepository(database=pg_db)

    version = pg_db.get_rows("SELECT VERSION()")

    logger.info(f"Connected: {version[0][0]}")

    try:
        # Set up the SQL database
        pg_db.execute("""DROP TABLE IF EXISTS websites_urls CASCADE""")
        pg_db.execute("""DROP TABLE IF EXISTS websites_metrics CASCADE""")

        pg_db.execute(
            """CREATE TABLE IF NOT EXISTS websites_urls(
                        id SERIAL PRIMARY KEY,
                        url TEXT NOT NULL UNIQUE,
                        content_regex VARCHAR(100)
                )"""
        )

        pg_db.execute(
            """CREATE TABLE IF NOT EXISTS websites_metrics(
                            id SERIAL PRIMARY KEY,
                            url_id INTEGER NOT NULL UNIQUE REFERENCES websites_urls(id),
                            status_code INTEGER NOT NULL,
                            response_time FLOAT NOT NULL,
                            page_content TEXT,
                            request_timestamp TIMESTAMP NOT NULL
                          )"""
        )

        pg_db.execute(
            """INSERT INTO websites_urls (url, content_regex)
            VALUES ('https://docs.aiohttp.org', 'regex_google')"""
        )
        pg_db.execute(
            """INSERT INTO websites_urls (url, content_regex)
            VALUES ('https://www.github.com', 'regex_github') returning id"""
        )

        logger.info("Running application:")
        metrics_client = MetricsClient()
        web_checker = WebsiteChecker(
            client=metrics_client,
            repository=repo,
            polling_interval=config.polling_interval,
            time_window=config.time_window,
            batch_size=config.batch_size,
        )
        web_checker.check_liveness()
        web_checker.collect_metrics()

    except Exception as e:
        logger.error(f"Stream failed: {e}")
        sys.exit(1)


# Keep the program running
# input("Press Enter to exit...\n")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
