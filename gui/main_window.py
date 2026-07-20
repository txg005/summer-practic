import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from datetime import datetime

from database import Database, CarsRepository, ClientsRepository, RentalsRepository, populate_sample_data
from gui.cars_tab import CarsTab
from gui.clients_tab import ClientsTab
from gui.rentals_tab import RentalsTab
from gui.reports_tab import ReportsTab

# Цветовая схема
BG_MAIN  = "#1a1a1a"
BG_CARD  = "#242424"
BG_NAV   = "#111111"
ACCENT   = "#FF8C00"
TEXT_PRI = "#FFFFFF"
TEXT_SEC = "#888888"
BORDER   = "#333333"


def _apply_ttk_dark_style():
    """Тёмная тема для ttk-виджетов (Treeview, Entry, Scrollbar и т.д.)"""
    st = ttk.Style()
    st.theme_use("clam")
    st.configure(".",                  background=BG_CARD,    foreground=TEXT_PRI, bordercolor=BORDER)
    st.configure("TFrame",             background=BG_CARD)
    st.configure("TLabelframe",        background=BG_CARD,    bordercolor=BORDER)
    st.configure("TLabelframe.Label",  background=BG_CARD,    foreground=TEXT_PRI)
    st.configure("TLabel",             background=BG_CARD,    foreground=TEXT_PRI)
    st.configure("TEntry",             fieldbackground="#2d2d2d", foreground=TEXT_PRI,
                                       insertcolor=TEXT_PRI,  bordercolor=BORDER)
    st.configure("TCombobox",          fieldbackground="#2d2d2d", foreground=TEXT_PRI,
                                       background="#2d2d2d",  bordercolor=BORDER)
    st.map("TCombobox",
           fieldbackground=[("readonly", "#2d2d2d")],
           selectbackground=[("focus", ACCENT)])
    st.configure("TButton",            background="#333333",  foreground=TEXT_PRI, bordercolor=BORDER)
    st.map("TButton",                  background=[("active", ACCENT)])
    st.configure("Treeview",           background="#1e1e1e",  foreground=TEXT_PRI,
                                       fieldbackground="#1e1e1e", rowheight=32)
    st.configure("Treeview.Heading",   background="#2d2d2d",  foreground=ACCENT,
                                       relief="flat")
    st.map("Treeview",
           background=[("selected", ACCENT)],
           foreground=[("selected", TEXT_PRI)])
    st.configure("TScrollbar",         background="#333333",  troughcolor=BG_MAIN,
                                       bordercolor=BORDER,    arrowcolor=TEXT_SEC)
    st.configure("TPanedwindow",       background=BG_MAIN)


class MainWindow:
    def __init__(self):
        ctk.set_appearance_mode("dark")

        self.root = ctk.CTk()
        self.root.title("Система аренды автомобилей")
        self.root.geometry("1200x750")
        self.root.configure(fg_color=BG_MAIN)

        _apply_ttk_dark_style()

        db = Database()
        populate_sample_data(db)

        self.cars_repo    = CarsRepository(db)
        self.clients_repo = ClientsRepository(db)
        self.rentals_repo = RentalsRepository(db)
        self.rentals_repo.activate_due_bookings(datetime.now().strftime('%Y-%m-%d %H:%M'))

        self._frames   = {}
        self._nav_btns = {}

        self._build_nav()
        self._build_content()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # Навигация
    def _build_nav(self):
        nav = tk.Frame(self.root, bg=BG_NAV, height=54)
        nav.pack(fill='x', side='top')
        nav.pack_propagate(False)

        # логотип
        logo = tk.Frame(nav, bg=BG_NAV)
        logo.pack(side='left', padx=(20, 0))
        tk.Label(logo, text="Авто",   bg=BG_NAV, fg=TEXT_PRI,
                 font=("Arial", 15, "bold")).pack(side='left')
        tk.Label(logo, text="Прокат", bg=BG_NAV, fg=ACCENT,
                 font=("Arial", 15, "bold")).pack(side='left')

        # вертикальный разделитель
        tk.Frame(nav, bg=BORDER, width=1).pack(side='left', fill='y', padx=14, pady=10)

        # кнопки вкладок
        tabs = [
            ("cars",    "Автомобили"),
            ("clients", "Клиенты"),
            ("rentals", "Аренда"),
            ("reports", "Отчёты"),
        ]
        for key, label in tabs:
            btn = tk.Button(
                nav, text=label,
                bg=BG_NAV, fg=TEXT_SEC,
                font=("Arial", 11), bd=0,
                padx=14, pady=4,
                activebackground=BG_CARD, activeforeground=ACCENT,
                cursor="hand2", relief="flat",
                takefocus=False,
                command=lambda k=key: self._show_tab(k)
            )
            btn.bind("<FocusIn>", lambda e: self.root.focus_set())
            btn.pack(side='left', padx=2, pady=8)
            self._nav_btns[key] = btn

        # нижняя линия-индикатор активной вкладки
        self._indicator = tk.Frame(self.root, bg=ACCENT, height=2)
        self._indicator.place(x=0, y=52, width=0)

    def _show_tab(self, key: str):
        for k, f in self._frames.items():
            f.pack_forget()
        self._frames[key].pack(fill='both', expand=True)

        for k, btn in self._nav_btns.items():
            is_active = (k == key)
            btn.configure(
                fg=ACCENT if is_active else TEXT_SEC,
                bg="#1e1e1e" if is_active else BG_NAV
            )

        # двигаем индикатор под активную кнопку
        btn = self._nav_btns[key]
        self.root.update_idletasks()
        x = btn.winfo_x() + btn.master.winfo_x()
        w = btn.winfo_width()
        self._indicator.place(x=x + 4, y=52, width=w - 8)

    # Контент
    def _build_content(self):
        self._content = tk.Frame(self.root, bg=BG_MAIN)
        self._content.pack(fill='both', expand=True)

        for key in ("cars", "clients", "rentals", "reports"):
            self._frames[key] = tk.Frame(self._content, bg=BG_MAIN)

        self.cars_tab = CarsTab(
            self._frames["cars"], self.cars_repo,
            on_cars_changed=lambda: self.rentals_tab.load_rental_combos()
        )
        self.clients_tab = ClientsTab(
            self._frames["clients"], self.clients_repo,
            on_clients_changed=lambda: self.rentals_tab.load_rental_combos()
        )
        self.rentals_tab = RentalsTab(
            self._frames["rentals"], self.rentals_repo,
            self.cars_repo, self.clients_repo,
            on_rental_changed=lambda: self.cars_tab.load_cars()
        )
        self.reports_tab = ReportsTab(self._frames["reports"], self.rentals_repo)

        self.root.after(150, lambda: self._show_tab("cars"))

    def _on_close(self):
        self.cars_repo.db.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()