"""Тесты для QuoteGenerator и модели Quote."""
import pytest

from models.quote import Quote
from models.exceptions import ThemeNotFoundError, EmptyThemeError
from services.quote_generator import QuoteGenerator


# ──────────── Фейковый репозиторий (без БД) ────────────
class FakeRepository:
    """Простой репозиторий в памяти для тестов.

    Настоящий QuoteRepository лезет в PostgreSQL — в тестах это
    лишнее. Подменяем фейком, который держит данные в словаре.
    """
    def __init__(self, data: dict):
        # data: {"Наука": [Quote, Quote, ...], ...}
        self._data = data

    def get_themes(self) -> list:
        return list(self._data.keys())

    def get_by_theme(self, theme: str) -> list:
        if theme not in self._data:
            raise ThemeNotFoundError(f"Тема '{theme}' не найдена")
        return self._data[theme]


# ──────────── Фикстуры: данные для тестов ────────────
@pytest.fixture
def sample_quotes():
    """Готовые объекты Quote для тестов."""
    return [
        Quote(id=1, text="Воображение важнее знания.", theme="Наука", author="Эйнштейн"),
        Quote(id=2, text="Скорость света — 300 000 км/с.", theme="Наука", author=None),
        Quote(id=3, text="Делай или не делай.", theme="Мотивация", author="Йода"),
    ]


@pytest.fixture
def repo_with_data(sample_quotes):
    """Репозиторий с цитатами по двум темам."""
    return FakeRepository({
        "Наука": [sample_quotes[0], sample_quotes[1]],
        "Мотивация": [sample_quotes[2]],
    })


@pytest.fixture
def empty_repo():
    """Репозиторий без единой темы."""
    return FakeRepository({})


# ──────────── Тесты QuoteGenerator ────────────
def test_generate_returns_quote_with_requested_theme(repo_with_data):
    """Генератор должен вернуть цитату именно запрошенной темы."""
    gen = QuoteGenerator(repo_with_data)
    q = gen.generate("Наука")
    assert q.theme == "Наука"
    assert "Наука" in q.text or q.author == "Эйнштейн"  # проверяем, что вернулась реальная цитата


def test_generate_unknown_theme_raises(empty_repo):
    """Запрос несуществующей темы → ThemeNotFoundError."""
    gen = QuoteGenerator(empty_repo)
    with pytest.raises(ThemeNotFoundError):
        gen.generate("Такой темы нет")


def test_generate_from_empty_theme_raises():
    """Тема существует, но в ней 0 цитат → EmptyThemeError."""
    repo = FakeRepository({"Пустая": []})
    gen = QuoteGenerator(repo)
    with pytest.raises(EmptyThemeError):
        gen.generate("Пустая")


def test_generate_randomness_within_theme(repo_with_data):
    """При нескольких вызовах должна быть возможность получить разные цитаты."""
    gen = QuoteGenerator(repo_with_data)
    results = set()
    for _ in range(50):
        q = gen.generate("Наука")
        results.add(q.id)
    # В теме 2 цитаты — за 50 попыток должны увидеть обе (с очень большой вероятностью)
    assert len(results) >= 2


# ──────────── Тесты модели Quote ────────────
def test_quote_valid(sample_quotes):
    """Объект создаётся с правильными атрибутами."""
    q = sample_quotes[0]
    assert q.id == 1
    assert q.text == "Воображение важнее знания."
    assert q.theme == "Наука"
    assert q.author == "Эйнштейн"


def test_quote_empty_text_raises():
    """Пустой текст цитаты → ValueError."""
    with pytest.raises(ValueError):
        Quote(id=1, text="", theme="Наука")


def test_quote_empty_theme_raises():
    """Пустая тема → ValueError."""
    with pytest.raises(ValueError):
        Quote(id=1, text="Цитата", theme="")


def test_quote_str_with_author(sample_quotes):
    """__str__ должен включать автора, если он есть."""
    q = sample_quotes[0]
    assert "Эйнштейн" in str(q)
    assert "Воображение" in str(q)


def test_quote_str_without_author():
    """__str__ без автора не должен писать «— None»."""
    q = Quote(id=1, text="Факт.", theme="Наука", author=None)
    s = str(q)
    assert "Факт." in s
    assert "None" not in s


def test_quote_as_dict(sample_quotes):
    """as_dict возвращает словарь со всеми полями."""
    q = sample_quotes[0]
    d = q.as_dict()
    assert d == {
        "id": 1,
        "text": "Воображение важнее знания.",
        "theme": "Наука",
        "author": "Эйнштейн",
    }