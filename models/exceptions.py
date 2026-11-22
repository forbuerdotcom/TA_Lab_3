class GeneratorError(Exception):
    """Базовое исключение генератора."""


class ThemeNotFoundError(GeneratorError):
    """Тема не найдена в базе."""


class EmptyThemeError(GeneratorError):
    """В теме нет ни одной цитаты."""


class DatabaseError(GeneratorError):
    """Ошибка работы с БД."""


class FavoriteError(GeneratorError):
    """Ошибка работы с избранным."""