from abc import ABC, abstractmethod
from config.settings import DATABASE_URL
from psycopg2.extras import execute_batch
from psycopg2.pool import ThreadedConnectionPool


class Database(ABC):
    @abstractmethod
    def execute_batch(query: str, argslist: list):
        pass

    @abstractmethod
    def get_rows(query: str):
        pass

    @abstractmethod
    def execute(self, query: str):
        pass


class PostgreSqlDatabase(Database):
    def __init__(self, dsn: str, min_con=1, max_con=100):
        self.pool = ThreadedConnectionPool(minconn=min_con, maxconn=max_con, dsn=dsn)

    def execute(self, query: str):
        conn = self.pool.getconn(self)
        try:
            with conn.cursor() as curs:
                curs.execute(query)
                conn.commit()
        finally:
            self.pool.putconn(conn)

    def execute_batch(self, query: str, argslist: list):
        conn = self.pool.getconn(self)
        try:
            with conn.cursor() as curs:
                execute_batch(curs, query, argslist)
                conn.commit()
        finally:
            self.pool.putconn(conn)

    def get_rows(self, query: str):
        conn = self.pool.getconn(self)
        try:
            with conn.cursor() as curs:
                curs.execute(query)
                return curs.fetchall()
        finally:
            self.pool.putconn(conn)


# can be used for unit tests
class TestDatabase(Database):
    def __init__(self, dsn: str):
        super.__init__(self, dsn)

    def execute_batch(query: str, argslist: list):
        print("Execute")

    def get_rows(query: str):
        print("GET")


if __name__ == "__main__":
    pg_db = PostgreSqlDatabase(dsn=DATABASE_URL)
    m = pg_db.get_rows("""SELECT * FROM websites_urls""")
    print(m)
