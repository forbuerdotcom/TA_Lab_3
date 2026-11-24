import psycopg2

from models.quote import Quote
from models.exceptions import DatabaseError


class HistoryService:
    def __init__(self, conn):
        self.conn = conn

    def add(self, quote: Quote):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO history (quote_id) VALUES (%s) RETURNING id, generated_at",
                    (quote.id,)
                )
                row = cur.fetchone()
                self.conn.commit()
                return row  # (history_id, generated_at)
        except psycopg2.Error as e:
            self.conn.rollback()
            raise DatabaseError(f"Ошибка записи истории: {e}") from e

    def get_recent(self, limit: int = 50) -> list[tuple]:
        """  возвращает список кортежей (id, time, theme, quote_text)."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT h.id, h.generated_at, t.name, q.text
                    FROM history h
                    JOIN quotes q ON h.quote_id = q.id
                    JOIN themes t ON q.theme_id = t.id
                    ORDER BY h.generated_at DESC
                    LIMIT %s
                """, (limit,))
                return cur.fetchall()
        except psycopg2.Error as e:
            raise DatabaseError(f"Ошибка чтения истории: {e}") from e

    def clear(self):
        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM history")
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise DatabaseError(f"Ошибка очистки истории: {e}") from e

    def count_by_theme(self) -> dict[str, int]:
        """для графика: сколько раз сгенерировали по каждой теме."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT t.name, COUNT(h.id)
                    FROM themes t
                    LEFT JOIN quotes q ON q.theme_id = t.id
                    LEFT JOIN history h ON h.quote_id = q.id
                    GROUP BY t.name
                    ORDER BY t.name
                """)
                return {row[0]: row[1] for row in cur.fetchall()}
        except psycopg2.Error as e:
            raise DatabaseError(f"Ошибка подсчёта активности: {e}") from e