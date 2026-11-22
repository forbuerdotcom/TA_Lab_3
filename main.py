import tkinter as tk
from tkinter import ttk


THEMES = ["Мотивация", "Наука", "История", "IT", "Философия", "Факты о животных"]


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Вариант №10. Генератор цитат/фактов с выбором тематики")
        self.geometry("900x650")

        self._build_menu()
        self._build_widgets()

    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Экспорт избранного...")
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.destroy)
        menubar.add_cascade(label="Файл", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Очистить историю")
        edit_menu.add_command(label="Очистить избранное")
        menubar.add_cascade(label="Правка", menu=edit_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Показать избранное")
        menubar.add_cascade(label="Вид", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе")
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.config(menu=menubar)

    def _build_widgets(self):
        # Заголовок
        self.TitleLabel = tk.Label(self, text="Генератор цитат/фактов", font=("Georgia", 20))
        self.TitleLabel.place(relx=0.5, rely=0.05, anchor="center")

        # Combobox выбора темы
        self.ThemeCombobox = ttk.Combobox(
            self, values=THEMES, state="readonly", font=("Georgia", 14)
        )
        self.ThemeCombobox.current(0)
        self.ThemeCombobox.place(relx=0.05, rely=0.14, relwidth=0.3)

        # Кнопки слева
        self.GenerateButton = tk.Button(self, text="Сгенерировать", font=("Georgia", 14))
        self.GenerateButton.place(relx=0.05, rely=0.22, relwidth=0.3, height=35)

        self.CopyButton = tk.Button(self, text="Скопировать", font=("Georgia", 14))
        self.CopyButton.place(relx=0.05, rely=0.29, relwidth=0.3, height=35)

        self.FavoriteButton = tk.Button(self, text="Добавить в избранное", font=("Georgia", 14))
        self.FavoriteButton.place(relx=0.05, rely=0.36, relwidth=0.3, height=35)

        self.ShowFavoriteButton = tk.Button(self, text="Показать избранное", font=("Georgia", 14))
        self.ShowFavoriteButton.place(relx=0.05, rely=0.43, relwidth=0.3, height=35)

        self.ClearHistoryButton = tk.Button(self, text="Очистить историю", font=("Georgia", 14))
        self.ClearHistoryButton.place(relx=0.05, rely=0.50, relwidth=0.3, height=35)

        self.ExitButton = tk.Button(self, text="Выход", font=("Georgia", 14), command=self.destroy)
        self.ExitButton.place(relx=0.05, rely=0.57, relwidth=0.3, height=35)

        # Поле с текущей цитатой
        self.ContentText = tk.Text(self, font=("Georgia", 14), state="disabled", wrap="word")
        self.ContentText.place(relx=0.40, rely=0.14, relwidth=0.55, relheight=0.15)

        # Заголовок таблицы истории
        self.HistoryLabel = tk.Label(self, text="История:", font=("Georgia", 12, "bold"))
        self.HistoryLabel.place(relx=0.40, rely=0.31)

        # Таблица истории
        self.HistoryTree = ttk.Treeview(
            self, columns=("time", "theme", "quote"), show="headings", height=8
        )
        self.HistoryTree.heading("time", text="Время")
        self.HistoryTree.heading("theme", text="Тема")
        self.HistoryTree.heading("quote", text="Цитата")
        self.HistoryTree.column("time", width=100, anchor="w")
        self.HistoryTree.column("theme", width=120, anchor="w")
        self.HistoryTree.column("quote", width=400, anchor="w")
        self.HistoryTree.place(relx=0.40, rely=0.34, relwidth=0.55, relheight=0.25)

        # Заголовок графика
        self.ChartLabel = tk.Label(self, text="График активности:", font=("Georgia", 12, "bold"))
        self.ChartLabel.place(relx=0.40, rely=0.61)

        # Место под график (пока просто рамка-заглушка)
        self.ChartFrame = tk.Frame(self, bg="white", bd=1, relief="solid")
        self.ChartFrame.place(relx=0.40, rely=0.64, relwidth=0.55, relheight=0.16)

        # Заголовок лога
        self.LogLabel = tk.Label(self, text="Лог:", font=("Georgia", 12, "bold"))
        self.LogLabel.place(relx=0.05, rely=0.66)

        # Лог
        self.LogText = tk.Text(self, font=("Consolas", 10), state="disabled")
        self.LogText.place(relx=0.05, rely=0.69, relwidth=0.30, relheight=0.25)


if __name__ == "__main__":
    MainWindow().mainloop()