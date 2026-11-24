"""Главное окно приложения."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from storage.quote_repository import QuoteRepository
from storage.favorite_service import FavoriteService
from storage.history_service import HistoryService
from services.quote_generator import QuoteGenerator
from models.exceptions import GeneratorError

DSN = "dbname=quote_generator user=postgres password=postgres host=localhost port=5432"


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Вариант №10. Генератор цитат/фактов с выбором тематики")
        self.geometry("900x720")

        # gодключение к БД
        self.repo = QuoteRepository(DSN)
        self.favorites = FavoriteService(self.repo.conn)
        self.history = HistoryService(self.repo.conn)
        self.generator = QuoteGenerator(self.repo)

        # текущая показанная цитата (объект Quote или None)
        self.current_quote = None

        self._build_menu()
        self._build_widgets()
        self._build_chart()
        self._refresh_themes()
        self._refresh_history()
        self._refresh_chart()
        self._log("Приложение запущено. БД подключена.")

    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Показать избранное", command=self.on_show_favorites)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_exit)
        menubar.add_cascade(label="Файл", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Очистить историю", command=self.on_clear_history)
        menubar.add_cascade(label="Правка", menu=edit_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.on_about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.config(menu=menubar)

    def _build_widgets(self):
        self.TitleLabel = tk.Label(self, text="Генератор цитат/фактов", font=("Georgia", 20))
        self.TitleLabel.place(relx=0.5, rely=0.04, anchor="center")

        self.ThemeCombobox = ttk.Combobox(self, state="readonly", font=("Georgia", 13))
        self.ThemeCombobox.place(relx=0.03, rely=0.12, relwidth=0.30)

        self.GenerateButton = tk.Button(self, text="Сгенерировать", font=("Georgia", 13),
                                        command=self.on_generate)
        self.GenerateButton.place(relx=0.03, rely=0.19, relwidth=0.30, height=32)

        self.CopyButton = tk.Button(self, text="Скопировать", font=("Georgia", 13),
                                    command=self.on_copy)
        self.CopyButton.place(relx=0.03, rely=0.25, relwidth=0.30, height=32)

        self.FavoriteButton = tk.Button(self, text="Добавить в избранное", font=("Georgia", 13),
                                        command=self.on_add_favorite)
        self.FavoriteButton.place(relx=0.03, rely=0.31, relwidth=0.30, height=32)

        self.ShowFavoriteButton = tk.Button(self, text="Показать избранное", font=("Georgia", 13),
                                            command=self.on_show_favorites)
        self.ShowFavoriteButton.place(relx=0.03, rely=0.37, relwidth=0.30, height=32)

        self.ClearHistoryButton = tk.Button(self, text="Очистить историю", font=("Georgia", 13),
                                            command=self.on_clear_history)
        self.ClearHistoryButton.place(relx=0.03, rely=0.43, relwidth=0.30, height=32)

        self.ExitButton = tk.Button(self, text="Выход", font=("Georgia", 13),
                                command=self.on_exit)
        self.ExitButton.place(relx=0.03, rely=0.49, relwidth=0.30, height=32)

        self.ContentText = tk.Text(self, font=("Georgia", 14), state="disabled", wrap="word")
        self.ContentText.place(relx=0.36, rely=0.12, relwidth=0.60, relheight=0.13)

        self.HistoryLabel = tk.Label(self, text="История:", font=("Georgia", 12, "bold"))
        self.HistoryLabel.place(relx=0.36, rely=0.27)
        self.HistoryTree = ttk.Treeview(
            self, columns=("time", "theme", "quote"), show="headings", height=8
        )
        self.HistoryTree.heading("time", text="Время")
        self.HistoryTree.heading("theme", text="Тема")
        self.HistoryTree.heading("quote", text="Цитата")
        self.HistoryTree.column("time", width=130, anchor="w")
        self.HistoryTree.column("theme", width=130, anchor="w")
        self.HistoryTree.column("quote", width=350, anchor="w")
        self.HistoryTree.place(relx=0.36, rely=0.30, relwidth=0.60, relheight=0.22)

        self.ChartLabel = tk.Label(self, text="График активности по темам:", font=("Georgia", 12, "bold"))
        self.ChartLabel.place(relx=0.36, rely=0.53)
        self.ChartFrame = tk.Frame(self, bg="white", bd=1, relief="solid")
        self.ChartFrame.place(relx=0.36, rely=0.56, relwidth=0.60, relheight=0.22)

        self.LogLabel = tk.Label(self, text="Лог:", font=("Georgia", 12, "bold"))
        self.LogLabel.place(relx=0.03, rely=0.56)
        self.LogText = tk.Text(self, font=("Consolas", 10), state="disabled")
        self.LogText.place(relx=0.03, rely=0.59, relwidth=0.30, relheight=0.35)


    def _build_chart(self):
        self.fig = Figure(figsize=(5, 2), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.ChartFrame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _refresh_chart(self):
        self.ax.clear()
        data = self.history.count_by_theme()
        themes = list(data.keys())
        counts = list(data.values())
        self.ax.bar(themes, counts, color="#3a7bd5")
        self.ax.set_ylabel("Кол-во")
        self.ax.tick_params(axis="x", labelrotation=30, labelsize=8)
        self.fig.tight_layout()
        self.canvas.draw()


    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        self.LogText.config(state="normal")
        self.LogText.insert("end", line)
        self.LogText.see("end")
        self.LogText.config(state="disabled")

    def _set_quote_text(self, text: str):
        self.ContentText.config(state="normal")
        self.ContentText.delete(1.0, "end")
        self.ContentText.insert("end", text)
        self.ContentText.config(state="disabled")

    def _refresh_themes(self):
        themes = self.repo.get_themes()
        self.ThemeCombobox["values"] = themes
        if themes:
            self.ThemeCombobox.current(0)

    def _refresh_history(self):
        for item in self.HistoryTree.get_children():
            self.HistoryTree.delete(item)
        rows = self.history.get_recent(50)
        for r in rows:
            # r = (id, generated_at, theme_name, quote_text)
            ts = r[1].strftime("%Y-%m-%d %H:%M:%S")
            quote = (r[3][:80] + "…") if len(r[3]) > 80 else r[3]
            self.HistoryTree.insert("", "end", values=(ts, r[2], quote))

    def on_generate(self):
        theme = self.ThemeCombobox.get()
        if not theme:
            messagebox.showwarning("Внимание", "Выберите тему")
            return
        try:
            quote = self.generator.generate(theme)
            self.current_quote = quote
            self._set_quote_text(str(quote))
            self.history.add(quote)
            self._refresh_history()
            self._refresh_chart()
            self._log(f"Сгенерирована цитата из темы «{theme}»")
        except GeneratorError as e:
            messagebox.showwarning("Генератор", str(e))
            self._log(f"Ошибка: {e}")

    def on_copy(self):
        if not self.current_quote:
            messagebox.showinfo("Копирование", "Сначала сгенерируйте цитату")
            return
        self.clipboard_clear()
        self.clipboard_append(str(self.current_quote))
        self._log("Цитата скопирована в буфер обмена")

    def on_add_favorite(self):
        if not self.current_quote:
            messagebox.showinfo("Избранное", "Сначала сгенерируйте цитату")
            return
        try:
            self.favorites.add(self.current_quote)
            self._log("Цитата добавлена в избранное")
        except GeneratorError as e:
            messagebox.showwarning("Избранное", str(e))
            self._log(f"Ошибка избранного: {e}")

    def on_show_favorites(self):
        FavoritesWindow(self)

    def on_clear_history(self):
        if messagebox.askyesno("Очистка", "Очистить всю историю?"):
            self.history.clear()
            self._refresh_history()
            self._refresh_chart()
            self._log("История очищена")

    def on_exit(self):
        self.repo.close()
        self.destroy()

    def on_about(self):
        messagebox.showinfo("О программе",
                            "Генератор цитат/фактов\nВариант №10\nЛабораторная работа №3")


class FavoritesWindow(tk.Toplevel):
    def __init__(self, master: MainWindow):
        super().__init__(master)
        self.master_win = master
        self.title("Избранное")
        self.geometry("620x450")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.FavoritesTree = ttk.Treeview(
            self, columns=("theme", "quote"), show="headings"
        )
        self.FavoritesTree.heading("theme", text="Тема")
        self.FavoritesTree.heading("quote", text="Цитата")
        self.FavoritesTree.column("theme", width=150, anchor="w")
        self.FavoritesTree.column("quote", width=440, anchor="w")
        self.FavoritesTree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        scrollbar = ttk.Scrollbar(self, command=self.FavoritesTree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=10)
        self.FavoritesTree.config(yscrollcommand=scrollbar.set)

        bottom = ttk.Frame(self)
        bottom.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))

        self.RemoveButton = tk.Button(bottom, text="Удалить выбранное",
                                      command=self.on_remove)
        self.RemoveButton.pack(side="left", padx=5)

        self.CloseButton = tk.Button(bottom, text="Закрыть", command=self.destroy)
        self.CloseButton.pack(side="right", padx=5)

        self._load_favorites()

    def _load_favorites(self):
        for item in self.FavoritesTree.get_children():
            self.FavoritesTree.delete(item)
        # Сохраняем id цитаты в iid строки Treeview, чтобы потом удалить
        try:
            favs = self.master_win.favorites.get_all()
            for q in favs:
                text = (q.text[:80] + "…") if len(q.text) > 80 else q.text
                self.FavoritesTree.insert("", "end", iid=str(q.id), values=(q.theme, text))
        except GeneratorError as e:
            messagebox.showwarning("Избранное", str(e))

    def on_remove(self):
        sel = self.FavoritesTree.selection()
        if not sel:
            messagebox.showinfo("Удаление", "Выберите цитату для удаления")
            return
        for item_id in sel:
            quote_id = int(item_id)
            try:
                self.master_win.favorites.remove(quote_id)
            except GeneratorError as e:
                messagebox.showwarning("Избранное", str(e))
        self._load_favorites()