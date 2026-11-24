"""Бизнес-логика: случайная цитата по теме."""
import random

from models.quote import Quote
from models.exceptions import ThemeNotFoundError, EmptyThemeError
from storage.quote_repository import QuoteRepository


class QuoteGenerator:
    def __init__(self, repository: QuoteRepository):
        self.repository = repository

    def generate(self, theme: str) -> Quote:
        # Сначала проверим, существует ли тема вообще
        themes = self.repository.get_themes()
        if theme not in themes:
            raise ThemeNotFoundError(f"Тема '{theme}' не найдена")

        quotes = self.repository.get_by_theme(theme)
        if not quotes:
            raise EmptyThemeError(f"В теме '{theme}' нет цитат")

        return random.choice(quotes)