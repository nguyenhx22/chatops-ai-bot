import psycopg2
from psycopg2.extras import RealDictCursor
import structlog
from core.config import settings

log = structlog.get_logger()


class PostgresDB:
    def __init__(self):
        self.connection = None

    def connect(self):
        if self.connection is None or self.connection.closed:
            try:
                self.connection = psycopg2.connect(
                    host=settings.PG_DB_HOST,
                    port=settings.PG_DB_PORT,
                    database=settings.PG_DB_NAME,
                    user=settings.PG_DB_USER,
                    password=settings.PG_DB_PASSWORD,
                )
            except Exception as e:
                log.error("Error connecting to PostgreSQL.", error=str(e))
                raise
        return self.connection

    def execute_query(self, query, params=None, fetch=True, dict_cursor=False):
        conn = self.connect()
        cursor_class = RealDictCursor if dict_cursor else None
        cursor = conn.cursor(cursor_factory=cursor_class)
        try:
            cursor.execute(query, params or ())
            if fetch:
                return cursor.fetchall()
            conn.commit()
            return None
        except Exception as e:
            log.error("Query execution failed", error=str(e), query=query)
            raise
        finally:
            cursor.close()

    def close(self):
        if self.connection and not self.connection.closed:
            self.connection.close()
