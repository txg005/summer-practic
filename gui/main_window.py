import tkinter as tk
from tkinter import ttk
from datetime import datetime

from database import (
    Database, CarsRepository, ClientsRepository, RentalsRepository, populate_sample_data
)
from gui.cars_tab import CarsTab
from gui.clients_tab import ClientsTab
from gui.rentals_tab import RentalsTab
from gui.reports_tab import ReportsTab

from gui.theme import apply_theme, BG_PRIMARY, BG_SECONDARY, ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, FONTS


class MainWindow:
    """Главное окно приложения с тёмной темой и верхним меню."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Система аренды автомобилей")
        self.root.geometry("1200x800")
        self.root.configure(bg=BG_PRIMARY)
        self.root.minsize(1000, 700)

        # Применяем тёмную тему
        apply_theme(self.root)

        # Настраиваем стиль скрытия вкладок для Notebook, чтобы использовать наше верхнее меню
        style = ttk.Style()
        style.layout('Tabless.TNotebook.Tab', [])

        # Оригинальная инициализация БД из первого файла
        db = Database()
        populate_sample_data(db)
        
        self.cars_repo = CarsRepository(db)
        self.clients_repo = ClientsRepository(db)
        self.rentals_repo = RentalsRepository(db)
        self.rentals_repo.activate_due_bookings(datetime.now().strftime('%Y-%m-%d %H:%M'))

        # ── Верхнее меню ──────────────────────────────────
        self.nav_buttons = {}
        self._build_navbar()

        # ── Контейнер для "страниц" ───────────────────────
        self.content_frame = tk.Frame(self.root, bg=BG_PRIMARY)
        self.content_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        # Создаём реальный ttk.Notebook, но без видимых стандартных вкладок
        self.notebook = ttk.Notebook(self.content_frame, style='Tabless.TNotebook')
        self.notebook.pack(fill='both', expand=True)

        # Оригинальная инициализация вкладок с сохранением всех аргументов, имен и колбэков
        self.cars_tab = CarsTab(
            self.notebook, self.cars_repo,
            on_cars_changed=lambda: self.rentals_tab.load_rental_combos()
        )
        self.clients_tab = ClientsTab(
            self.notebook, self.clients_repo,
            on_clients_changed=lambda: self.rentals_tab.load_rental_combos()
        )
        self.rentals_tab = RentalsTab(
            self.notebook, self.rentals_repo, self.cars_repo, self.clients_repo,
            on_rental_changed=lambda: self.cars_tab.load_cars()
        )
        self.reports_tab = ReportsTab(self.notebook, self.rentals_repo)

        # Открываем первую вкладку по умолчанию
        self.show_tab("cars")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_navbar(self):
        """Создать верхнее навигационное меню."""
        navbar = tk.Frame(self.root, bg=BG_SECONDARY, height=56)
        navbar.pack(fill='x', padx=0, pady=0)
        navbar.pack_propagate(False)

        # Логотип / заголовок
        title = tk.Label(
            navbar,
            text="CarRental",
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY,
            font=FONTS["title"],
        )
        title.pack(side='left', padx=(20, 40), pady=10)

        # Пункты меню
        menu_items = [
            ("cars",     "Автомобили"),
            ("clients",  "Клиенты"),
            ("rentals",  "Аренда"),
            ("reports",  "Отчёты"),
        ]

        for tab_id, label in menu_items:
            btn = tk.Label(
                navbar,
                text=label,
                bg=BG_SECONDARY,
                fg=TEXT_SECONDARY,
                font=FONTS["normal"],
                cursor="hand2",
                padx=20,
                pady=16,
            )
            btn.pack(side='left')
            btn.bind("<Button-1>", lambda e, tid=tab_id: self.show_tab(tid))
            btn.bind("<Enter>",  lambda e, b=btn: b.configure(fg=TEXT_PRIMARY))
            btn.bind("<Leave>",  lambda e, b=btn: b.configure(
                fg=ACCENT if b == self.nav_buttons.get(self.current_tab) else TEXT_SECONDARY
            ))
            self.nav_buttons[tab_id] = btn

        # Разделитель под меню
        separator = tk.Frame(self.root, bg="#2a2a45", height=1)
        separator.pack(fill='x')

    def show_tab(self, tab_id: str):
        """Переключить видимую вкладку в скрытом Notebook."""
        self.current_tab = tab_id

        # Индексы вкладок в порядке их добавления в ttk.Notebook
        tab_indices = {
            "cars": 0,
            "clients": 1,
            "rentals": 2,
            "reports": 3
        }
        
        index = tab_indices.get(tab_id, 0)
        self.notebook.select(index)

        # Обновить стили кнопок навигации (активная / неактивные)
        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                btn.configure(fg=ACCENT, font=(FONTS["bold"][0], FONTS["bold"][1], "bold"))
            else:
                btn.configure(fg=TEXT_SECONDARY, font=FONTS["normal"])

    def _on_close(self):
        self.cars_repo.db.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()