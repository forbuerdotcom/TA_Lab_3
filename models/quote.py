class Quote:
    def __init__(self, id: int, text: str, theme: str, author: str | None = None):
        if not text:
            raise ValueError("Текст цитаты не может быть пустым")
        if not theme:
            raise ValueError("Тема не может быть пустой")

        self.id = id
        self.text = text
        self.theme = theme
        self.author = author

    def __repr__(self) -> str:
        return f"Quote(id={self.id}, theme={self.theme!r}, author={self.author!r}, text={self.text!r})"

    def __str__(self) -> str:
        if self.author:
            return f"«{self.text}»\n— {self.author}"
        return f"«{self.text}»"

    def as_dict(self) -> dict:
        return {"id": self.id, "text": self.text, "theme": self.theme, "author": self.author}