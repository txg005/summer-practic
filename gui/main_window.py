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


class MainWindow:
    """Главное окно приложения
    Создаёт репозитории и вкладки, связывает их через callbacks"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Система аренды автомобилей")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')

        db = Database()
        populate_sample_data(db)
        
        self.cars_repo = CarsRepository(db)
        self.clients_repo = ClientsRepository(db)
        self.rentals_repo = RentalsRepository(db)
        self.rentals_repo.activate_due_bookings(datetime.now().strftime('%Y-%m-%d %H:%M'))

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.cars_tab = CarsTab(
            notebook, self.cars_repo,
            on_cars_changed=lambda: self.rentals_tab.load_rental_combos()
        )
        self.clients_tab = ClientsTab(
            notebook, self.clients_repo,
            on_clients_changed=lambda: self.rentals_tab.load_rental_combos()
        )
        self.rentals_tab = RentalsTab(
            notebook, self.rentals_repo, self.cars_repo, self.clients_repo,
            on_rental_changed=lambda: self.cars_tab.load_cars()
        )
        self.reports_tab = ReportsTab(notebook, self.rentals_repo)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.cars_repo.db.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()