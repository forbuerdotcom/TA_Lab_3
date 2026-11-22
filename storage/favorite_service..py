import psycopg2

from models.quote import Quote
from models.exceptions import FavoriteError, DatabaseError


class FavoriteService:
    def __init__(self, conn):
        self.conn = conn

    def add(self, quote: Quote):
        try:
            with self.conn.cursor() as cur:
                # Проверяем, не в избранном ли уже эта цитата
                cur.execute("SELECT id FROM favorites WHERE quote_id = %s", (quote.id,))
                if cur.fetchone() is not None:
                    raise FavoriteError("Эта цитата уже в избранном")
                cur.execute(
                    "INSERT INTO favorites (quote_id) VALUES (%s) RETURNING id",
                    (quote.id,)
                )
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise DatabaseError(f"Ошибка добавления в избранное: {e}") from e

    def get_all(self) -> list[Quote]:
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT q.id, q.text, q.author, t.name, f.added_at
                    FROM favorites f
                    JOIN quotes q ON f.quote_id = q.id
                    JOIN themes t ON q.theme_id = t.id
                    ORDER BY f.added_at DESC
                """)
                rows = cur.fetchall()
        except psycopg2.Error as e:
            raise DatabaseError(f"Ошибка чтения избранного: {e}") from e

        return [Quote(id=r[0], text=r[1], theme=r[3], author=r[2]) for r in rows]

    def remove(self, quote_id: int):
        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM favorites WHERE quote_id = %s", (quote_id,))
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise DatabaseError(f"Ошибка удаления из избранного: {e}") from e