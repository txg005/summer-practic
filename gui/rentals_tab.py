import tkinter as tk
from dataclasses import astuple
from datetime import datetime
from tkinter import ttk, messagebox
from typing import Callable
from tkcalendar import DateEntry

from database import Rental, CarsRepository, ClientsRepository, RentalsRepository
from utils import Tooltip


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
        start_frame = ttk.Frame(form_frame)
        start_frame.grid(row=1, column=1, padx=5, pady=5)
        self.rental_start_date = DateEntry(start_frame, width=12, date_pattern='yyyy-mm-dd')
        self.rental_start_date.pack(side='left')
        self.rental_start_hour = ttk.Combobox(start_frame, values=[f'{h:02d}' for h in range(24)], width=4)
        self.rental_start_hour.pack(side='left', padx=(5, 0))
        self.rental_start_hour.set('10')
        ttk.Label(start_frame, text=":").pack(side='left')
        self.rental_start_minute = ttk.Combobox(start_frame, values=['00', '15', '30', '45'], width=4)
        self.rental_start_minute.pack(side='left')
        self.rental_start_minute.set('00')

        ttk.Label(form_frame, text="Дата окончания:").grid(row=1, column=2, sticky='w', padx=5, pady=5)
        self.rental_end_date = DateEntry(form_frame, width=12, date_pattern='yyyy-mm-dd')
        self.rental_end_date.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(form_frame, text="Стоимость:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.rental_cost = ttk.Entry(form_frame, width=25)
        self.rental_cost.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(form_frame, text="Рассчитать стоимость", command=self.calculate_cost).grid(
            row=2, column=2, padx=5, pady=5)

        # Кнопки
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=3, column=0, columnspan=4, pady=10)

        ttk.Button(buttons_frame, text="Создать аренду", command=self.add_rental).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Обновить аренду", command=self.update_rental).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Завершить аренду", command=self.complete_rental).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Отменить аренду", command=self.cancel_rental).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Очистить", command=self.clear_rental_form).pack(side='left', padx=5)
        _search_btn = ttk.Button(buttons_frame, text="Поиск", command=self.search_rentals)
        _search_btn.pack(side='left', padx=5)
        Tooltip(_search_btn,
            "При поиске учитываются:\n"
            "  • автомобиль\n  • клиент\n"
            "  • дата начала / окончания\n    (без учёта времени)\n"
            "  • стоимость\n\n"
            "Не учитываются:\n  • статус аренды")
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
        cars = self.cars_repo.get_all()
        self.rental_car['values'] = [f"{c.id} - {c.brand} {c.model} ({c.license_plate})" for c in cars]

        clients = self.clients_repo.get_all()
        self.rental_client['values'] = [f"{cl.id} - {cl.full_name}" for cl in clients]

    def _filter_cars(self, event):
        """Фильтрация автомобилей при вводе"""
        typed = self.rental_car.get()
        if len(typed) < 2:
            self.load_rental_combos()
            return
        cars = self.cars_repo.filter_all(typed)
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

            start_date = datetime.strptime(self.rental_start_date.get(), '%Y-%m-%d')
            end_date = datetime.strptime(self.rental_end_date.get(), '%Y-%m-%d')

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
            start_dt = f"{self.rental_start_date.get()} {f"{self.rental_start_hour.get()}:{self.rental_start_minute.get()}"}"
            end_dt = f"{self.rental_end_date.get()} {f"{self.rental_start_hour.get()}:{self.rental_start_minute.get()}"}"  # то же время

            today = datetime.now().strftime('%Y-%m-%d %H:%M')
            if start_dt < today:
                messagebox.showerror("Ошибка", "Дата начала не может быть раньше текущего момента!")
                return

            is_future = start_dt > today
            car = self.cars_repo.get_by_id(car_id)

            if not is_future and car.status != 'доступен':
                messagebox.showerror("Ошибка", "Автомобиль недоступен для аренды!")
                return

            if self.rentals_repo.has_date_conflict(car_id, start_dt, end_dt):
                messagebox.showerror("Ошибка", "На эти даты автомобиль уже арендован или забронирован!")
                return

            rental = Rental(
                car_id=car_id, client_id=client_id,
                start_date=start_dt, end_date=end_dt,
                total_cost=float(self.rental_cost.get()),
                status='забронировано' if is_future else 'активная'
            )
            self.rentals_repo.insert(rental)
            if not is_future:
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

    def update_rental(self):
        selected = self.rentals_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите аренду для обновления!")
            return
        try:
            start_dt = f"{self.rental_start_date.get()} {f"{self.rental_start_hour.get()}:{self.rental_start_minute.get()}"}"
            end_dt = f"{self.rental_end_date.get()} {f"{self.rental_start_hour.get()}:{self.rental_start_minute.get()}"}"
            rental_id = self.rentals_tree.item(selected[0])['values'][0]
            old_rental = self.rentals_repo.get_by_id(rental_id)
            car_text = self.rental_car.get()
            client_text = self.rental_client.get()
            if not car_text or not client_text:
                messagebox.showerror("Ошибка", "Выберите автомобиль и клиента!")
                return
            new_car_id = int(car_text.split(' - ')[0])
            new_client_id = int(client_text.split(' - ')[0])
            rental = Rental(
                id=rental_id, car_id=new_car_id, client_id=new_client_id,
                start_date=start_dt, end_date=end_dt,
                total_cost=float(self.rental_cost.get()), status=old_rental.status
            )
            if self.rentals_repo.has_date_conflict(
                    new_car_id, start_dt, end_dt,
                    exclude_rental_id=rental_id):
                messagebox.showerror("Ошибка", "На эти даты автомобиль уже арендован или забронирован!")
                return
            self.rentals_repo.update(rental)
            if old_rental.car_id != new_car_id:
                self.cars_repo.update_status(old_rental.car_id, 'доступен')
                if old_rental.status == 'активная':
                    self.cars_repo.update_status(new_car_id, 'арендован')
            self.load_rentals()
            self.load_rental_combos()
            self.on_rental_changed()
            messagebox.showinfo("Успех", "Аренда обновлена!")
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность ввода данных!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при обновлении аренды: {str(e)}")

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
        self.rental_start_date.set_date(datetime.now())
        self.rental_start_hour.set('10')
        self.rental_start_minute.set('00')
        self.rental_end_date.set_date(datetime.now())
        self.rental_cost.delete(0, tk.END)

    def _on_rental_select(self, event):
        """Обработка выбора аренды"""
        selected = self.rentals_tree.selection()
        if not selected:
            return
        rental_id = self.rentals_tree.item(selected[0])['values'][0]
        rental = self.rentals_repo.get_by_id(rental_id)
        if not rental:
            return
        car = self.cars_repo.get_by_id(rental.car_id)
        client = self.clients_repo.get_by_id(rental.client_id)
        self.rental_car.set(f"{car.id} - {car.brand} {car.model} ({car.license_plate})" if car else '')
        self.rental_client.set(f"{client.id} - {client.full_name}" if client else '')
        start_date_part, start_time_part = rental.start_date.rsplit(' ', 1)
        self.rental_start_date.set_date(datetime.strptime(start_date_part, '%Y-%m-%d'))
        hour_part, minute_part = start_time_part.split(':')
        self.rental_start_hour.set(hour_part)
        self.rental_start_minute.set(minute_part)
        self.rental_end_date.set_date(datetime.strptime(rental.end_date.split(' ')[0], '%Y-%m-%d'))
        self.rental_cost.delete(0, tk.END)
        self.rental_cost.insert(0, f"{rental.total_cost:.2f}")

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
                data.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d %H:%M') if x[0] else datetime.min,
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
        start_date = self.rental_start_date.get().strip()
        end_date = self.rental_end_date.get().strip()

        car_raw = self.rental_car.get().strip()
        car_search = car_raw.split(' - ', 1)[1] if ' - ' in car_raw else car_raw

        client_raw = self.rental_client.get().strip()
        client_search = client_raw.split(' - ', 1)[1] if ' - ' in client_raw else client_raw

        cost = self.rental_cost.get().strip()

        try:
            rentals = self.rentals_repo.search(
                start_date=start_date, end_date=end_date,
                car_text=car_search, client_text=client_search, cost=cost
            )
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