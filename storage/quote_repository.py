"""Слой работы с базой данных: чтение тем и цитат."""
import psycopg2

from models.quote import Quote
from models.exceptions import ThemeNotFoundError, DatabaseError


class QuoteRepository:
    """Читает темы и цитаты из PostgreSQL."""

    def __init__(self, dsn: str):
        # dsn вида: "dbname=quote_generator user=postgres password=postgres host=localhost port=5432"
        try:
            self.conn = psycopg2.connect(dsn)
        except psycopg2.Error as e:
            raise DatabaseError(f"Не удалось подключиться к БД: {e}") from e

    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()

    def get_themes(self) -> list[str]:
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT name FROM themes ORDER BY id")
                return [row[0] for row in cur.fetchall()]
        except psycopg2.Error as e:
            raise DatabaseError(f"Ошибка чтения тем: {e}") from e

    def get_by_theme(self, theme_name: str) -> list[Quote]:
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT q.id, q.text, q.author, t.name
                    FROM quotes q
                    JOIN themes t ON q.theme_id = t.id
                    WHERE t.name = %s
                    ORDER BY q.id
                """, (theme_name,))
                rows = cur.fetchall()
        except psycopg2.Error as e:
            raise DatabaseError(f"Ошибка чтения цитат: {e}") from e

        if not rows:
            raise ThemeNotFoundError(f"Тема '{theme_name}' не найдена или пуста")

        return [Quote(id=r[0], text=r[1], theme=r[3], author=r[2]) for r in rows]