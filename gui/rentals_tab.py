import tkinter as tk
from dataclasses import astuple
from datetime import datetime
from tkinter import ttk, messagebox
from typing import Callable

from database import Rental, CarsRepository, ClientsRepository, RentalsRepository


class RentalsTab:
    """Вкладка 'Аренда' """

    def __init__(self, notebook: ttk.Notebook, rentals_repo: RentalsRepository,
                 cars_repo: CarsRepository, clients_repo: ClientsRepository,
                 on_rental_changed: Callable[[], None]):
        self.rentals_repo = rentals_repo
        self.cars_repo = cars_repo
        self.clients_repo = clients_repo
        self.on_rental_changed = on_rental_changed
        self.sort_column = None
        self.sort_reverse = False

        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Аренда")

        self._create_widgets()
        self.load_rentals()
        self.load_rental_combos()

    def _create_widgets(self):
        # Фрейм для формы
        form_frame = ttk.LabelFrame(self.frame, text="Новая аренда")
        form_frame.pack(fill='x', padx=5, pady=5)

        # Поля формы
        ttk.Label(form_frame, text="Автомобиль:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.rental_car = ttk.Combobox(form_frame, width=25)
        self.rental_car.grid(row=0, column=1, padx=5, pady=5)
        self.rental_car.bind('<KeyRelease>', self._filter_cars)

        ttk.Label(form_frame, text="Клиент:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.rental_client = ttk.Combobox(form_frame, width=25)
        self.rental_client.grid(row=0, column=3, padx=5, pady=5)
        self.rental_client.bind('<KeyRelease>', self._filter_clients)

        ttk.Label(form_frame, text="Дата начала:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.rental_start = ttk.Entry(form_frame, width=25)
        self.rental_start.grid(row=1, column=1, padx=5, pady=5)
        self.rental_start.insert(0, datetime.now().strftime('%Y-%m-%d'))

        ttk.Label(form_frame, text="Дата окончания:").grid(row=1, column=2, sticky='w', padx=5, pady=5)
        self.rental_end = ttk.Entry(form_frame, width=25)
        self.rental_end.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(form_frame, text="Стоимость:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.rental_cost = ttk.Entry(form_frame, width=25)
        self.rental_cost.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(form_frame, text="Рассчитать стоимость", command=self.calculate_cost).grid(
            row=2, column=2, padx=5, pady=5)

        # Кнопки
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=3, column=0, columnspan=4, pady=10)

        ttk.Button(buttons_frame, text="Создать аренду", command=self.add_rental).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Завершить аренду", command=self.complete_rental).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Отменить аренду", command=self.cancel_rental).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Очистить", command=self.clear_rental_form).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Поиск", command=self.search_rentals).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Сбросить", command=self.reset_rentals_search).pack(side='left', padx=5)

        # Таблица аренды
        self.rentals_tree = ttk.Treeview(
            self.frame,
            columns=('ID', 'Автомобиль', 'Клиент', 'Дата начала', 'Дата окончания', 'Стоимость', 'Статус'),
            show='headings'
        )
        self.rentals_tree.pack(fill='both', expand=True, padx=5, pady=5)

        # Сортировка по заголовкам
        for col in self.rentals_tree['columns']:
            self.rentals_tree.heading(col, text=col, command=lambda c=col: self.sort_rentals_tree(c))

        # Заголовки столбцов
        for col in self.rentals_tree['columns']:
            self.rentals_tree.heading(col, text=col)
            self.rentals_tree.column(col, width=120)

        # Привязка событий
        self.rentals_tree.bind('<ButtonRelease-1>', self._on_rental_select)

    # --- Комбобоксы ---

    def load_rental_combos(self):
        """Загрузка данных для комбобоксов"""
        cars = self.cars_repo.get_available()
        self.rental_car['values'] = [f"{c.id} - {c.brand} {c.model} ({c.license_plate})" for c in cars]

        clients = self.clients_repo.get_all()
        self.rental_client['values'] = [f"{cl.id} - {cl.full_name}" for cl in clients]

    def _filter_cars(self, event):
        """Фильтрация автомобилей при вводе"""
        typed = self.rental_car.get()
        if len(typed) < 2:
            self.load_rental_combos()
            return
        cars = self.cars_repo.filter_available(typed)
        self.rental_car['values'] = [f"{c.id} - {c.brand} {c.model} ({c.license_plate})" for c in cars]

    def _filter_clients(self, event):
        """Фильтрация клиентов при вводе"""
        typed = self.rental_client.get()
        if len(typed) < 2:
            self.load_rental_combos()
            return
        clients = self.clients_repo.filter_by_name(typed)
        self.rental_client['values'] = [f"{cl.id} - {cl.full_name}" for cl in clients]

    # --- CRUD аренды ---

    def calculate_cost(self):
        """Расчёт стоимости аренды"""
        try:
            car_text = self.rental_car.get()
            if not car_text:
                messagebox.showwarning("Предупреждение", "Выберите автомобиль!")
                return

            start_date = datetime.strptime(self.rental_start.get(), '%Y-%m-%d')
            end_date = datetime.strptime(self.rental_end.get(), '%Y-%m-%d')

            if end_date <= start_date:
                messagebox.showerror("Ошибка", "Дата окончания должна быть позже даты начала!")
                return

            # Извлекаем ID автомобиля из текста комбобокса
            car_id = int(car_text.split(' - ')[0])
            car = self.cars_repo.get_by_id(car_id)

            # Расчёт количества дней
            days = (end_date - start_date).days
            total_cost = days * car.daily_rate

            self.rental_cost.delete(0, tk.END)
            self.rental_cost.insert(0, f"{total_cost:.2f}")

        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты! Используйте YYYY-MM-DD")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при расчете: {str(e)}")

    def add_rental(self):
        """Создание аренды"""
        try:
            car_text = self.rental_car.get()
            client_text = self.rental_client.get()

            if not car_text or not client_text:
                messagebox.showerror("Ошибка", "Выберите автомобиль и клиента!")
                return

            car_id = int(car_text.split(' - ')[0])
            client_id = int(client_text.split(' - ')[0])

            # Проверяем доступность автомобиля
            car = self.cars_repo.get_by_id(car_id)
            if car.status != 'доступен':
                messagebox.showerror("Ошибка", "Автомобиль недоступен для аренды!")
                return
            
            # Проверяем дату начала аренды
            if self.rental_start.get() < datetime.now().strftime('%Y-%m-%d'):
                messagebox.showerror("Ошибка", "Дата начала не может быть раньше сегодняшнего дня!")
                return

            # Создаем аренду
            rental = Rental(
                car_id=car_id, client_id=client_id,
                start_date=self.rental_start.get(), end_date=self.rental_end.get(),
                total_cost=float(self.rental_cost.get()), status='активная'
            )
            self.rentals_repo.insert(rental)
            self.cars_repo.update_status(car_id, 'арендован')

            self.load_rentals()
            self.load_rental_combos()
            self.on_rental_changed()
            self.clear_rental_form()
            messagebox.showinfo("Успех", "Аренда создана!")

        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность ввода данных!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании аренды: {str(e)}")

    def complete_rental(self):
        """Завершение аренды"""
        selected = self.rentals_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите аренду для завершения!")
            return

        try:
            rental_id = self.rentals_tree.item(selected[0])['values'][0]
            rental = self.rentals_repo.get_by_id(rental_id)

            self.rentals_repo.update_status(rental_id, 'завершенная')
            self.cars_repo.update_status(rental.car_id, 'доступен')

            self.load_rentals()
            self.load_rental_combos()
            self.on_rental_changed()
            messagebox.showinfo("Успех", "Аренда завершена!")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при завершении аренды: {str(e)}")

    def cancel_rental(self):
        """Отмена аренды"""
        selected = self.rentals_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите аренду для отмены!")
            return

        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите отменить аренду?"):
            try:
                rental_id = self.rentals_tree.item(selected[0])['values'][0]
                rental = self.rentals_repo.get_by_id(rental_id)

                self.rentals_repo.update_status(rental_id, 'отменена')
                self.cars_repo.update_status(rental.car_id, 'доступен')

                self.load_rentals()
                self.load_rental_combos()
                self.on_rental_changed()
                messagebox.showinfo("Успех", "Аренда отменена!")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при отмене аренды: {str(e)}")

    def clear_rental_form(self):
        """Очистка формы аренды"""
        self.rental_car.set('')
        self.rental_client.set('')
        self.rental_start.delete(0, tk.END)
        self.rental_start.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.rental_end.delete(0, tk.END)
        self.rental_cost.delete(0, tk.END)

    def _on_rental_select(self, event):
        """Обработка выбора аренды"""
        pass  # Дополнительная функциональность при необходимости

    def sort_rentals_tree(self, col):
        """Сортировка таблицы аренды с реверсом"""
        # Определяем направление сортировки
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
        self.sort_column = col

        # Собираем данные для сортировки
        data = [(self.rentals_tree.set(child, col), child) for child in self.rentals_tree.get_children('')]

        # Сортируем данные с учетом направления
        try:
            if col in ['ID', 'Стоимость']:
                data.sort(key=lambda x: float(x[0]) if x[0] else 0, reverse=self.sort_reverse)
            elif col in ['Дата начала', 'Дата окончания']:
                # Для пустых дат используем минимально возможную дату
                data.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d') if x[0] else datetime.min,
                          reverse=self.sort_reverse)
            else:
                data.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)
        except (ValueError, TypeError):
            data.sort(key=lambda x: str(x[0]).lower(), reverse=self.sort_reverse)

        # Перемещаем строки в отсортированном порядке
        for index, (val, child) in enumerate(data):
            self.rentals_tree.move(child, '', index)

        # Обновляем заголовки для визуального отображения сортировки
        for c in self.rentals_tree['columns']:
            text = self.rentals_tree.heading(c, 'text').replace(' ▲', '').replace(' ▼', '')
            if c == col:
                text += ' ▼' if self.sort_reverse else ' ▲'
            self.rentals_tree.heading(c, text=text)

    def search_rentals(self):
        """Поиск аренды"""
        start_date = self.rental_start.get().strip()
        end_date = self.rental_end.get().strip()

        try:
            rentals = self.rentals_repo.search(start_date=start_date, end_date=end_date)
            for item in self.rentals_tree.get_children():
                self.rentals_tree.delete(item)
            for rental in rentals:
                self.rentals_tree.insert('', 'end', values=astuple(rental))

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка поиска: {str(e)}")
            self.load_rentals()

    def reset_rentals_search(self):
        """Сброс поиска аренды"""
        self.load_rentals()
        for c in self.rentals_tree['columns']:
            text = self.rentals_tree.heading(c, 'text').replace(' ▲', '').replace(' ▼', '')
            self.rentals_tree.heading(c, text=text)

    def load_rentals(self):
        """Загрузка списка аренды"""
        for item in self.rentals_tree.get_children():
            self.rentals_tree.delete(item)
        for rental in self.rentals_repo.get_all_with_details():
            self.rentals_tree.insert('', 'end', values=astuple(rental))