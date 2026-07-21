import tkinter as tk
from dataclasses import astuple
from datetime import datetime
from tkinter import ttk, messagebox
from typing import Callable
import customtkinter as ctk
from gui.ctk_calendar import CTkDatePicker
from gui.theme import (BG_MAIN, BG_CARD, BG_INPUT, ACCENT, ACCENT_HOVER,
                       TEXT_PRI, TEXT_SEC, BORDER, BTN_SEC, BTN_SEC_HVR,
                       BTN_DEL, BTN_DEL_HVR)

from database import Rental, CarsRepository, ClientsRepository, RentalsRepository
from utils import Tooltip


class RentalsTab:
    """Вкладка 'Аренда' """

    def __init__(self, parent_frame, rentals_repo: RentalsRepository,
                 cars_repo: CarsRepository, clients_repo: ClientsRepository,
                 on_rental_changed: Callable[[], None]):
        self.rentals_repo = rentals_repo
        self.cars_repo = cars_repo
        self.clients_repo = clients_repo
        self.on_rental_changed = on_rental_changed
        self.sort_column = None
        self.sort_reverse = False

        self.frame = tk.Frame(parent_frame, bg=BG_MAIN)
        self.frame.pack(fill='both', expand=True)

        self._create_widgets()
        self.load_rentals()
        self.load_rental_combos()

    def _create_widgets(self):
        entry_kw = dict(fg_color=BG_INPUT, border_color=BORDER,
                        text_color=TEXT_PRI, placeholder_text_color=TEXT_SEC,
                        height=34, corner_radius=6)
        combo_kw = dict(fg_color=BG_INPUT, border_color=BORDER,
                        button_color=BORDER, button_hover_color=ACCENT,
                        text_color=TEXT_PRI, dropdown_fg_color=BG_CARD,
                        dropdown_text_color=TEXT_PRI,
                        dropdown_hover_color=ACCENT,
                        height=34, corner_radius=6)
        btn_pri = dict(height=34, corner_radius=8,
                    fg_color=ACCENT,  hover_color=ACCENT_HOVER)
        btn_sec = dict(height=34, corner_radius=8,
                    fg_color=BTN_SEC, hover_color=BTN_SEC_HVR, text_color=TEXT_PRI)
        btn_del = dict(height=34, corner_radius=8,
                    fg_color=BTN_DEL, hover_color=BTN_DEL_HVR, text_color=TEXT_PRI)
        btn_ok  = dict(height=34, corner_radius=8,
                    fg_color="#1a5c2a", hover_color="#236b33", text_color=TEXT_PRI)

        def label(parent, text):
            ctk.CTkLabel(parent, text=text, text_color=TEXT_SEC,
                        font=ctk.CTkFont(size=12)).pack(anchor='w', pady=(4, 2))

        def sep(parent):
            ctk.CTkFrame(parent, fg_color=BORDER, height=1,
                        corner_radius=0).pack(fill='x', padx=16, pady=8)

        # Карточка формы
        card = ctk.CTkFrame(self.frame, fg_color=BG_CARD, corner_radius=12)
        card.pack(fill='x', padx=16, pady=(12, 6))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill='x', padx=16, pady=(12, 0))
        ctk.CTkLabel(hdr, text="Аренда",
                    text_color=TEXT_PRI,
                    font=ctk.CTkFont(size=14, weight="bold")).pack(side='left')
        ctk.CTkButton(hdr, text="Сбросить", width=90,
                    command=self.reset_rentals_search, **btn_sec).pack(side='right', padx=(4, 0))
        _sb = ctk.CTkButton(hdr, text="Поиск", width=90,
                            command=self.search_rentals, **btn_pri)
        _sb.pack(side='right', padx=(4, 4))
        Tooltip(_sb,
            "При поиске учитываются:\n"
            "  • автомобиль\n  • клиент\n"
            "  • дата начала / окончания\n    (без учёта времени)\n"
            "  • стоимость\n\n"
            "Не учитываются:\n  • статус аренды")

        sep(card)

        # строка 1: авто + клиент
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill='x', padx=16)
        row1.columnconfigure((0, 1), weight=1)

        col_car = ctk.CTkFrame(row1, fg_color="transparent")
        col_car.grid(row=0, column=0, sticky='ew', padx=(0, 6))
        label(col_car, "Автомобиль")
        self.rental_car = ctk.CTkComboBox(col_car, **combo_kw)
        self.rental_car.pack(fill='x')
        self.rental_car.bind('<KeyRelease>', self._filter_cars)
        self._setup_combo_placeholder(self.rental_car)

        col_cl = ctk.CTkFrame(row1, fg_color="transparent")
        col_cl.grid(row=0, column=1, sticky='ew', padx=(6, 0))
        label(col_cl, "Клиент")
        self.rental_client = ctk.CTkComboBox(col_cl, **combo_kw)
        self.rental_client.pack(fill='x')
        self.rental_client.bind('<KeyRelease>', self._filter_clients)
        self._setup_combo_placeholder(self.rental_client)

        # строка 2: даты + время
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill='x', padx=16, pady=(0, 4))
        row2.columnconfigure((0, 1), weight=1)

        # Дата начала + время
        col_start = ctk.CTkFrame(row2, fg_color="transparent")
        col_start.grid(row=0, column=0, sticky='ew', padx=(0, 6))
        label(col_start, "Дата и время начала")
        start_inner = ctk.CTkFrame(col_start, fg_color="transparent")
        start_inner.pack(fill='x')
        self.rental_start_date = CTkDatePicker(start_inner, height=34)
        self.rental_start_date.pack(side='left', fill='x', expand=True, padx=(0, 4))
        self.rental_start_hour = ctk.CTkComboBox(
            start_inner, values=[f'{h:02d}' for h in range(24)],
            width=64, **combo_kw)
        self.rental_start_hour.pack(side='left', padx=(0, 2))
        self.rental_start_hour.set('10')
        ctk.CTkLabel(start_inner, text=":", text_color=TEXT_PRI,
                    font=ctk.CTkFont(size=14, weight="bold")).pack(side='left')
        self.rental_start_minute = ctk.CTkComboBox(
            start_inner, values=['00', '15', '30', '45'],
            width=64, **combo_kw)
        self.rental_start_minute.pack(side='left', padx=(2, 0))
        self.rental_start_minute.set('00')

        # Дата окончания
        col_end = ctk.CTkFrame(row2, fg_color="transparent")
        col_end.grid(row=0, column=1, sticky='ew', padx=(6, 0))
        label(col_end, "Дата окончания (время = время начала)")
        self.rental_end_date = CTkDatePicker(col_end, height=34)
        self.rental_end_date.pack(fill='x')

        # строка 3: стоимость
        row3 = ctk.CTkFrame(card, fg_color="transparent")
        row3.pack(fill='x', padx=16, pady=(0, 4))

        col_cost = ctk.CTkFrame(row3, fg_color="transparent")
        col_cost.pack(side='left', fill='x', expand=True, padx=(0, 8))
        label(col_cost, "Стоимость (BYN)")
        self.rental_cost = ctk.CTkEntry(col_cost, placeholder_text="0.00", **entry_kw)
        self.rental_cost.pack(fill='x')

        col_calc = ctk.CTkFrame(row3, fg_color="transparent")
        col_calc.pack(side='left', padx=(0, 0))
        ctk.CTkLabel(col_calc, text=" ", font=ctk.CTkFont(size=12)).pack(anchor='w', pady=(4, 2))
        ctk.CTkButton(col_calc, text="Рассчитать стоимость", width=180,
                    command=self.calculate_cost, **btn_sec).pack()

        # кнопки
        sep(card)
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(padx=16, pady=(0, 12), anchor='w')

        ctk.CTkButton(btns, text="Создать аренду",   width=130, command=self.add_rental,      **btn_pri).pack(side='left', padx=(0, 6))
        ctk.CTkButton(btns, text="Обновить аренду",  width=130, command=self.update_rental,    **btn_sec).pack(side='left', padx=6)
        ctk.CTkButton(btns, text="Завершить аренду", width=140, command=self.complete_rental,  **btn_ok ).pack(side='left', padx=6)
        ctk.CTkButton(btns, text="Отменить аренду",  width=130, command=self.cancel_rental,    **btn_del).pack(side='left', padx=6)
        ctk.CTkButton(btns, text="Очистить",         width=100, command=self.clear_rental_form,**btn_sec).pack(side='left', padx=6)

        # Таблица
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        style.configure("Treeview",
                        background=BG_CARD,
                        fieldbackground=BG_CARD,
                        foreground=TEXT_PRI,
                        borderwidth=0,
                        relief="flat",
                        rowheight=34)

        # Подсветка выбранной строки оранжевым
        style.map("Treeview",
                  background=[('selected', ACCENT)],
                  foreground=[('selected', '#ffffff')])

        # Заголовки таблицы
        style.configure("Treeview.Heading",
                        bg=BG_CARD,
                        foreground=ACCENT,
                        font=("Segoe UI", 10, "bold"),
                        borderwidth=0,
                        relief="flat")

        # Сохраняем оранжевый цвет заголовков при наведении мышкой
        style.map("Treeview.Heading",
                  background=[('active', '#2c2c3b')],
                  foreground=[('active', ACCENT)])

        # --- КОНТЕЙНЕР ТАБЛИЦЫ И СКРОЛЛБАР ---
        tree_card = ctk.CTkFrame(self.frame, fg_color=BG_CARD, corner_radius=12)
        tree_card.pack(fill='both', expand=True, padx=16, pady=(0, 12))

        tree_wrap = ctk.CTkFrame(tree_card, fg_color="transparent")
        tree_wrap.pack(fill='both', expand=True, padx=10, pady=10)

        cols = ('ID', 'Автомобиль', 'Клиент',
                'Дата начала', 'Дата окончания', 'Стоимость', 'Статус')
        
        self.rentals_tree = ttk.Treeview(tree_wrap, columns=cols, show='headings', style="Treeview")
        self.rentals_tree.pack(fill='both', expand=True, side='left')

        # Цвета чередования строк
        self.rentals_tree.tag_configure('odd',         background='#1e1e1e')
        self.rentals_tree.tag_configure('even',        background='#252525')
        self.rentals_tree.tag_configure('active',      foreground='#4CAF50')
        self.rentals_tree.tag_configure('booked',      foreground='#FF8C00')
        self.rentals_tree.tag_configure('completed',   foreground='#888888')
        self.rentals_tree.tag_configure('cancelled',   foreground='#e74c3c')

        widths = {'ID': 45, 'Стоимость': 90, 'Статус': 110,
                'Дата начала': 130, 'Дата окончания': 130}
        for col in cols:
            self.rentals_tree.heading(col, text=col,
                                    command=lambda c=col: self.sort_rentals_tree(c))
            self.rentals_tree.column(col, width=widths.get(col, 160), minwidth=50)

        # Кастомный плоский скроллбар CustomTkinter
        sb = ctk.CTkScrollbar(tree_wrap, 
                              orientation='vertical', 
                              command=self.rentals_tree.yview,
                              fg_color="transparent",
                              button_color=BORDER,
                              button_hover_color="#a0a0a0",
                              )
        
        sb.pack(side='right', fill='y', padx=(6, 0))
        self.rentals_tree.configure(yscrollcommand=sb.set)

        # Бинды событий
        self.rentals_tree.bind('<ButtonRelease-1>', self._on_rental_select)
        self.rentals_tree.bind('<MouseWheel>', lambda e:
            self.rentals_tree.yview_scroll(int(-1*(e.delta/120)), 'units'))

        # выравнивание
        self.rentals_tree.column('ID',             anchor='center', width=10)
        self.rentals_tree.column('Дата начала',    anchor='center')
        self.rentals_tree.column('Дата окончания', anchor='center')
        self.rentals_tree.column('Стоимость',      anchor='center')
        self.rentals_tree.column('Статус',         anchor='center', width=160)

    # --- Комбобоксы ---

    def _setup_combo_placeholder(self, combo, placeholder='Выберите...'):
        combo.set(placeholder)
        combo.configure(text_color=TEXT_SEC)

        def on_focus_in(event):
            if combo.get() == placeholder:
                combo.set('')
                combo.configure(text_color=TEXT_PRI)

        def on_focus_out(event):
            if combo.get().strip() == '':
                combo.set(placeholder)
                combo.configure(text_color=TEXT_SEC)

        def on_select(value):
            combo.configure(text_color=TEXT_PRI)

        combo.configure(command=on_select)
        combo._entry.bind('<FocusIn>',  on_focus_in)
        combo._entry.bind('<FocusOut>', on_focus_out)
        
    def load_rental_combos(self):
        """Загрузка данных для комбобоксов"""
        cars = self.cars_repo.get_all()
        self.rental_car.configure(values = [f"{c.id} - {c.brand} {c.model} ({c.license_plate})" for c in cars])

        clients = self.clients_repo.get_all()
        self.rental_client.configure(values = [f"{cl.id} - {cl.full_name}" for cl in clients])

    def _filter_cars(self, event):
        """Фильтрация автомобилей при вводе"""
        typed = self.rental_car.get()
        if len(typed) < 2:
            self.load_rental_combos()
            return
        cars = self.cars_repo.filter_all(typed)
        self.rental_car.configure(values = [f"{c.id} - {c.brand} {c.model} ({c.license_plate})" for c in cars])

    def _filter_clients(self, event):
        """Фильтрация клиентов при вводе"""
        typed = self.rental_client.get()
        if len(typed) < 2:
            self.load_rental_combos()
            return
        clients = self.clients_repo.filter_by_name(typed)
        self.rental_client.configure(values = [f"{cl.id} - {cl.full_name}" for cl in clients])

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
        self.rental_car.set('Выберите...')
        self.rental_car.configure(text_color=TEXT_SEC)
        self.rental_client.set('Выберите...')
        self.rental_client.configure(text_color=TEXT_SEC)
        self.rental_start_date.set_date(datetime.now())
        self.rental_start_hour.set('10')
        self.rental_start_minute.set('00')
        self.rental_end_date.set_date(datetime.now())
        self.rental_cost.delete(0, 'end')
        self.rental_cost.configure(placeholder_text="0.00")

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
        self.rental_cost.delete(0, 'end')
        self.rental_cost.insert(0, f"{rental.total_cost:.2f}")
        self.rental_car.configure(text_color=TEXT_PRI)
        self.rental_client.configure(text_color=TEXT_PRI)

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

        # перекрашиваем строки после изменения их порядка
        self._recolor_rows()    

    def _recolor_rows(self):
            """Восстанавливает правильное чередование цветов строк после сортировки"""
            for index, item in enumerate(self.rentals_tree.get_children()):
                # Получаем список текущих тегов строки (чтобы не удалить теги статуса)
                tags = list(self.rentals_tree.item(item, 'tags'))
                
                # Удаляем старые теги четности, если они есть
                if 'even' in tags: tags.remove('even')
                if 'odd' in tags:  tags.remove('odd')
                
                # Добавляем правильный тег в зависимости от нового порядкового номера
                tags.append('even' if index % 2 == 0 else 'odd')
                
                # Применяем обновленные теги обратно к строке
                self.rentals_tree.item(item, tags=tags)

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

            self._recolor_rows()

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
        for item in self.rentals_tree.get_children():
            self.rentals_tree.delete(item)

        STATUS_TAG = {
            'активная':     'active',
            'забронировано':'booked',
            'завершенная':  'completed',
            'отменена':     'cancelled',
        }
        for i, rental in enumerate(self.rentals_repo.get_all_with_details()):
            row_tag   = 'even' if i % 2 == 0 else 'odd'
            status_tag = STATUS_TAG.get(rental.status, '')
            self.rentals_tree.insert('', 'end', values=astuple(rental),
                                    tags=(row_tag, status_tag))