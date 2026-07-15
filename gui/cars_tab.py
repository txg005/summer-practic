import sqlite3
import tkinter as tk
from dataclasses import astuple
from datetime import datetime
from tkinter import ttk, messagebox
from typing import Callable

from database import Car, CarsRepository
from utils import validate_belarusian_license_plate
from utils import Tooltip


class CarsTab:
    """Вкладка 'Автомобили' """

    def __init__(self, notebook: ttk.Notebook, cars_repo: CarsRepository, on_cars_changed: Callable[[], None]):
        self.cars_repo = cars_repo
        self.on_cars_changed = on_cars_changed
        self.sort_column = None
        self.sort_reverse = False

        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Автомобили")

        self._create_widgets()
        self.load_cars()

    def _create_widgets(self):
        # Фрейм для формы
        form_frame = ttk.LabelFrame(self.frame, text="Добавить/Редактировать автомобиль")
        form_frame.pack(fill='x', padx=5, pady=5)

        # Поля формы
        ttk.Label(form_frame, text="Марка:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.car_brand = ttk.Entry(form_frame, width=20)
        self.car_brand.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Модель:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.car_model = ttk.Entry(form_frame, width=20)
        self.car_model.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form_frame, text="Год:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.car_year = ttk.Entry(form_frame, width=20)
        self.car_year.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Номер:").grid(row=1, column=2, sticky='w', padx=5, pady=5)
        self.car_license = ttk.Entry(form_frame, width=20)
        self.car_license.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(form_frame, text="Цена/день (BYN):").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.car_rate = ttk.Entry(form_frame, width=20)
        self.car_rate.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Статус:").grid(row=2, column=2, sticky='w', padx=5, pady=5)
        self.car_status = ttk.Combobox(form_frame, values=['все', 'доступен', 'арендован', 'на ТО'], width=17)
        self.car_status.grid(row=2, column=3, padx=5, pady=5)
        self.car_status.set('доступен')

        ttk.Label(form_frame, text="Последнее ТО:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.car_maintenance = ttk.Entry(form_frame, width=20)
        self.car_maintenance.grid(row=3, column=1, padx=5, pady=5)
        self.car_maintenance.insert(0, datetime.now().strftime('%Y-%m-%d'))

        # Кнопки
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=4, column=0, columnspan=4, pady=10)

        ttk.Button(buttons_frame, text="Добавить", command=self.add_car).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Обновить", command=self.update_car).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Удалить", command=self.delete_car).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Очистить", command=self.clear_car_form).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Отметить ТО", command=self.mark_maintenance).pack(side='left', padx=5)
        _search_btn = ttk.Button(buttons_frame, text="Поиск", command=self.search_cars)
        _search_btn.pack(side='left', padx=5)
        Tooltip(_search_btn,
            "При поиске учитываются:\n"
            "  • марка\n  • модель\n  • год\n"
            "  • номер\n  • цена/день\n  • статус\n\n"
            "Не учитываются:\n  • последнее ТО")
        ttk.Button(buttons_frame, text="Сбросить", command=self.reset_cars_search).pack(side='left', padx=5)

        # Таблица автомобилей
        self.cars_tree = ttk.Treeview(
            self.frame,
            columns=('ID', 'Марка', 'Модель', 'Год', 'Номер', 'Цена/день', 'Статус', 'Последнее ТО'),
            show='headings'
        )
        self.cars_tree.pack(fill='both', expand=True, padx=5, pady=5)

        # Сортировка по заголовкам
        for col in self.cars_tree['columns']:
            self.cars_tree.heading(col, text=col, command=lambda c=col: self.sort_cars_tree(c))

        for col in self.cars_tree['columns']:
            self.cars_tree.heading(col, text=col)
            self.cars_tree.column(col, width=100)

        # Привязка событий
        self.cars_tree.bind('<ButtonRelease-1>', self.on_car_select)
        
        # Скроллбар
        cars_scrollbar = ttk.Scrollbar(self.frame, orient='vertical', command=self.cars_tree.yview)
        cars_scrollbar.pack(side='right', fill='y')
        self.cars_tree.configure(yscrollcommand=cars_scrollbar.set)

    def add_car(self):
        """Добавление автомобиля"""
        try:
            brand = self.car_brand.get().strip()
            model = self.car_model.get().strip()
            year = int(self.car_year.get())
            license_plate = self.car_license.get().strip()
            daily_rate = float(self.car_rate.get())
            status = self.car_status.get()
            last_maintenance=self.car_maintenance.get().strip() or datetime.now().strftime('%Y-%m-%d')

            # Валидация
            if not all([brand, model, year, license_plate, daily_rate]):
                messagebox.showerror("Ошибка", "Все поля должны быть заполнены!")
                return

            if not validate_belarusian_license_plate(license_plate):
                messagebox.showerror("Ошибка", "Неверный формат номера автомобиля! Пример: 1234 AB-7")
                return

            if year < 1900 or year > datetime.now().year + 1:
                messagebox.showerror("Ошибка", "Неверный год выпуска!")
                return

            if daily_rate <= 0:
                messagebox.showerror("Ошибка", "Цена аренды должна быть больше 0!")
                return

            car = Car(brand=brand, model=model, year=year, license_plate=license_plate,
                      daily_rate=daily_rate, status=status,
                      last_maintenance=last_maintenance)
            self.cars_repo.insert(car)

            self.load_cars()
            self.on_cars_changed()
            self.clear_car_form()
            messagebox.showinfo("Успех", "Автомобиль добавлен!")

        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность ввода числовых значений!")
        except sqlite3.IntegrityError:
            messagebox.showerror("Ошибка", "Автомобиль с таким номером уже существует!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при добавлении: {str(e)}")

    def update_car(self):
        """Обновление автомобиля"""
        selected = self.cars_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите автомобиль для обновления!")
            return

        try:
            car_id = self.cars_tree.item(selected[0])['values'][0]
            brand = self.car_brand.get().strip()
            model = self.car_model.get().strip()
            year = int(self.car_year.get())
            license_plate = self.car_license.get().strip()
            daily_rate = float(self.car_rate.get())
            status = self.car_status.get()
            last_maintenance=self.car_maintenance.get().strip() or None

            # Валидация
            if not all([brand, model, year, license_plate, daily_rate]):
                messagebox.showerror("Ошибка", "Все поля должны быть заполнены!")
                return

            if not validate_belarusian_license_plate(license_plate):
                messagebox.showerror("Ошибка", "Неверный формат номера автомобиля! Пример: 1234 AB-7")
                return

            if year < 1900 or year > datetime.now().year + 1:
                messagebox.showerror("Ошибка", "Неверный год выпуска!")
                return

            if daily_rate <= 0:
                messagebox.showerror("Ошибка", "Цена аренды должна быть больше 0!")
                return

            car = Car(id=car_id, brand=brand, model=model, year=year,
                      license_plate=license_plate, daily_rate=daily_rate, status=status, last_maintenance=last_maintenance)
            self.cars_repo.update(car)

            self.load_cars()
            self.on_cars_changed()
            messagebox.showinfo("Успех", "Автомобиль обновлен!")

        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность ввода числовых значений!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при обновлении: {str(e)}")

    def delete_car(self):
        """Удаление автомобиля"""
        selected = self.cars_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите автомобиль для удаления!")
            return

        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить автомобиль?"):
            try:
                car_id = self.cars_tree.item(selected[0])['values'][0]
                self.cars_repo.delete(car_id)
                self.load_cars()
                self.on_cars_changed()
                self.clear_car_form()
                messagebox.showinfo("Успех", "Автомобиль удален!")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при удалении: {str(e)}")

    def mark_maintenance(self):
        """Отметка о ТО"""
        selected = self.cars_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите автомобиль!")
            return

        try:
            car_id = self.cars_tree.item(selected[0])['values'][0]
            self.cars_repo.mark_maintenance(car_id, datetime.now().strftime('%Y-%m-%d'))

            self.load_cars()
            messagebox.showinfo("Успех", "Отметка о ТО добавлена!")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка: {str(e)}")

    def clear_car_form(self):
        """Очистка формы автомобиля"""
        self.car_brand.delete(0, tk.END)
        self.car_model.delete(0, tk.END)
        self.car_year.delete(0, tk.END)
        self.car_license.delete(0, tk.END)
        self.car_rate.delete(0, tk.END)
        self.car_status.set('доступен')
        self.car_maintenance.delete(0, tk.END)
        self.car_maintenance.insert(0, datetime.now().strftime('%Y-%m-%d'))

    def on_car_select(self, event):
        """Обработка выбора автомобиля"""
        selected = self.cars_tree.selection()
        if selected:
            values = self.cars_tree.item(selected[0])['values']
            self.car_brand.delete(0, tk.END)
            self.car_brand.insert(0, values[1])
            self.car_model.delete(0, tk.END)
            self.car_model.insert(0, values[2])
            self.car_year.delete(0, tk.END)
            self.car_year.insert(0, values[3])
            self.car_license.delete(0, tk.END)
            self.car_license.insert(0, values[4])
            self.car_rate.delete(0, tk.END)
            self.car_rate.insert(0, values[5])
            self.car_status.set(values[6])
            self.car_maintenance.delete(0, tk.END)
            self.car_maintenance.insert(0, values[7] if values[7] else '')

    def sort_cars_tree(self, col):
        """Сортировка таблицы автомобилей с реверсом"""
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
        self.sort_column = col

        data = [(self.cars_tree.set(child, col), child) for child in self.cars_tree.get_children('')]

        try:
            if col in ['ID', 'Год', 'Цена/день']:
                data.sort(key=lambda x: float(x[0]) if x[0] else 0, reverse=self.sort_reverse)
            else:
                data.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)
        except (ValueError, TypeError):
            data.sort(key=lambda x: str(x[0]).lower(), reverse=self.sort_reverse)

        for index, (val, child) in enumerate(data):
            self.cars_tree.move(child, '', index)

        for c in self.cars_tree['columns']:
            text = self.cars_tree.heading(c, 'text').replace(' ▲', '').replace(' ▼', '')
            if c == col:
                text += ' ▼' if self.sort_reverse else ' ▲'
            self.cars_tree.heading(c, text=text)

    def search_cars(self):
        """Поиск автомобилей"""
        brand = self.car_brand.get().strip()
        model = self.car_model.get().strip()
        year = self.car_year.get().strip()
        license_plate = self.car_license.get().strip()
        rate = self.car_rate.get().strip()
        status = self.car_status.get()

        try:
            cars = self.cars_repo.search(brand=brand, model=model, license_plate=license_plate,
                                          status=status, year=year, rate=rate)

            for item in self.cars_tree.get_children():
                self.cars_tree.delete(item)
            for car in cars:
                self.cars_tree.insert('', 'end', values=astuple(car))

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка поиска: {str(e)}")
            self.load_cars()

    def reset_cars_search(self):
        """Сброс поиска автомобилей"""
        self.load_cars()
        for c in self.cars_tree['columns']:
            text = self.cars_tree.heading(c, 'text')
            text = text.replace(' ▲', '').replace(' ▼', '')
            self.cars_tree.heading(c, text=text)

    def load_cars(self):
        """Загрузка списка автомобилей"""
        for item in self.cars_tree.get_children():
            self.cars_tree.delete(item)

        for car in self.cars_repo.get_all():
            self.cars_tree.insert('', 'end', values=astuple(car))