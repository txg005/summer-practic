import sqlite3
import tkinter as tk
from dataclasses import astuple
from datetime import datetime
from tkinter import ttk, messagebox
from typing import Callable
import customtkinter as ctk
from gui.theme import (BG_MAIN, BG_CARD, BG_INPUT, ACCENT, ACCENT_HOVER,
                       TEXT_PRI, TEXT_SEC, BORDER, BTN_SEC, BTN_SEC_HVR,
                       BTN_DEL, BTN_DEL_HVR)

from database import Car, CarsRepository
from utils import validate_belarusian_license_plate
from utils import Tooltip


class CarsTab:
    """Вкладка 'Автомобили' """

    def __init__(self, parent_frame, cars_repo: CarsRepository, on_cars_changed: Callable[[], None]):
        self.cars_repo = cars_repo
        self.on_cars_changed = on_cars_changed
        self.sort_column = None
        self.sort_reverse = False

        self.frame = tk.Frame(parent_frame, bg=BG_MAIN)
        self.frame.pack(fill='both', expand=True)

        self._create_widgets()
        self.load_cars()

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
                    fg_color=ACCENT,   hover_color=ACCENT_HOVER)
        btn_sec = dict(height=34, corner_radius=8,
                    fg_color=BTN_SEC,  hover_color=BTN_SEC_HVR, text_color=TEXT_PRI)
        btn_del = dict(height=34, corner_radius=8,
                    fg_color=BTN_DEL,  hover_color=BTN_DEL_HVR, text_color=TEXT_PRI)

        def field(parent, label_text, col, row=0, padleft=0, padright=0):
            """Создаёт колонку с подписью — возвращает фрейм."""
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=row, column=col, sticky='ew',
                padx=(padleft, padright), pady=2)
            ctk.CTkLabel(f, text=label_text, text_color=TEXT_SEC,
                        font=ctk.CTkFont(size=12)).pack(anchor='w', pady=(4, 2))
            return f

        # Карточка формы
        card = ctk.CTkFrame(self.frame, fg_color=BG_CARD, corner_radius=12)
        card.pack(fill='x', padx=16, pady=(12, 6))

        # заголовок + поиск/сброс
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill='x', padx=16, pady=(12, 0))
        ctk.CTkLabel(hdr, text="Автомобиль",
                    text_color=TEXT_PRI,
                    font=ctk.CTkFont(size=14, weight="bold")).pack(side='left')
        ctk.CTkButton(hdr, text="Сбросить", width=90,
                    command=self.reset_cars_search, **btn_sec).pack(side='right', padx=(4, 0))
        _sb = ctk.CTkButton(hdr, text="Поиск", width=90,
                            command=self.search_cars, **btn_pri)
        _sb.pack(side='right', padx=(4, 4))
        Tooltip(_sb,
                "При поиске учитываются:\n"
                "  • марка\n  • модель\n  • год\n"
                "  • номер\n  • цена/день\n  • статус\n\n"
                "Не учитываются:\n  • последнее ТО")

        ctk.CTkFrame(card, fg_color=BORDER, height=1,
                    corner_radius=0).pack(fill='x', padx=16, pady=8)

        # поля — строка 1
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill='x', padx=16)
        row1.columnconfigure((0, 1, 2), weight=1)

        f = field(row1, "Марка", 0, padright=6)
        self.car_brand = ctk.CTkEntry(f, placeholder_text="Toyota", **entry_kw)
        self.car_brand.pack(fill='x')

        f = field(row1, "Модель", 1, padleft=6, padright=6)
        self.car_model = ctk.CTkEntry(f, placeholder_text="Camry", **entry_kw)
        self.car_model.pack(fill='x')

        f = field(row1, "Год", 2, padleft=6)
        self.car_year = ctk.CTkEntry(f, placeholder_text="2020", **entry_kw)
        self.car_year.pack(fill='x')

        # поля — строка 2
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill='x', padx=16, pady=(0, 4))
        row2.columnconfigure((0, 1, 2, 3), weight=1)

        f = field(row2, "Гос. номер", 0, padright=6)
        self.car_license = ctk.CTkEntry(f, placeholder_text="1234 AB-7", **entry_kw)
        self.car_license.pack(fill='x')

        f = field(row2, "Цена/день (BYN)", 1, padleft=6, padright=6)
        self.car_rate = ctk.CTkEntry(f, placeholder_text="150.00", **entry_kw)
        self.car_rate.pack(fill='x')

        f = field(row2, "Статус", 2, padleft=6, padright=6)
        self.car_status = ctk.CTkComboBox(
            f, values=['все', 'доступен', 'арендован', 'на ТО'], **combo_kw)
        self.car_status.pack(fill='x')
        self.car_status.set('доступен')

        f = field(row2, "Последнее ТО", 3, padleft=6)
        self.car_maintenance = ctk.CTkEntry(f, placeholder_text="YYYY-MM-DD", **entry_kw)
        self.car_maintenance.pack(fill='x')
        self.car_maintenance.insert(0, datetime.now().strftime('%Y-%m-%d'))

        # кнопки CRUD
        ctk.CTkFrame(card, fg_color=BORDER, height=1,
                    corner_radius=0).pack(fill='x', padx=16, pady=(6, 8))
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(padx=16, pady=(0, 12), anchor='w')

        ctk.CTkButton(btns, text="Добавить",    width=110, command=self.add_car,          **btn_pri).pack(side='left', padx=(0, 6))
        ctk.CTkButton(btns, text="Обновить",    width=110, command=self.update_car,        **btn_sec).pack(side='left', padx=6)
        ctk.CTkButton(btns, text="Удалить",     width=110, command=self.delete_car,        **btn_del).pack(side='left', padx=6)
        ctk.CTkButton(btns, text="Очистить",    width=110, command=self.clear_car_form,    **btn_sec).pack(side='left', padx=6)
        ctk.CTkButton(btns, text="Отметить ТО", width=120, command=self.mark_maintenance,  **btn_sec).pack(side='left', padx=6)

        # Таблица
        tree_card = ctk.CTkFrame(self.frame, fg_color=BG_CARD, corner_radius=12)
        tree_card.pack(fill='both', expand=True, padx=16, pady=(0, 12))

        tree_wrap = tk.Frame(tree_card, bg=BG_CARD)
        tree_wrap.pack(fill='both', expand=True, padx=8, pady=8)

        cols = ('ID', 'Марка', 'Модель', 'Год', 'Номер',
                'Цена/день', 'Статус', 'Последнее ТО')
        self.cars_tree = ttk.Treeview(tree_wrap, columns=cols, show='headings')
        self.cars_tree.pack(fill='both', expand=True, side='left')

        self.cars_tree.tag_configure('odd',         background='#1e1e1e')
        self.cars_tree.tag_configure('even',        background='#252525')

        widths = {'ID': 45, 'Год': 60, 'Цена/день': 95, 'Статус': 100, 'Последнее ТО': 110}
        for col in cols:
            self.cars_tree.heading(col, text=col,
                                command=lambda c=col: self.sort_cars_tree(c))
            self.cars_tree.column(col, width=widths.get(col, 110), minwidth=50, anchor='center')

        # Кастомный плоский скроллбар CustomTkinter
        sb = ctk.CTkScrollbar(tree_wrap, 
                              orientation='vertical', 
                              command=self.cars_tree.yview,
                              fg_color="transparent",
                              button_color=BORDER,
                              button_hover_color="#a0a0a0",
                              )
        
        sb.pack(side='right', fill='y', padx=(6, 0))
        self.cars_tree.configure(yscrollcommand=sb.set)

        # Бинды событий
        self.cars_tree.bind('<ButtonRelease-1>', self.on_car_select)
        self.cars_tree.bind('<MouseWheel>', lambda e:
            self.cars_tree.yview_scroll(int(-1*(e.delta/120)), 'units'))

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
        self.car_brand.delete(0, 'end')
        self.car_model.delete(0, 'end')
        self.car_year.delete(0, 'end')
        self.car_license.delete(0, 'end')
        self.car_rate.delete(0, 'end')
        self.car_status.set('доступен')
        self.car_maintenance.delete(0, 'end')
        self.car_maintenance.insert(0, datetime.now().strftime('%Y-%m-%d'))

    def on_car_select(self, event):
        """Обработка выбора автомобиля"""
        selected = self.cars_tree.selection()
        if selected:
            values = self.cars_tree.item(selected[0])['values']
            self.car_brand.delete(0, 'end')
            self.car_brand.insert(0, values[1])
            self.car_model.delete(0, 'end')
            self.car_model.insert(0, values[2])
            self.car_year.delete(0, 'end')
            self.car_year.insert(0, values[3])
            self.car_license.delete(0, 'end')
            self.car_license.insert(0, values[4])
            self.car_rate.delete(0, 'end')
            self.car_rate.insert(0, values[5])
            self.car_status.set(values[6])
            self.car_maintenance.delete(0, 'end')
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

        self._recolor_rows()    

    def _recolor_rows(self):
            """Восстанавливает правильное чередование цветов строк после сортировки"""
            for index, item in enumerate(self.cars_tree.get_children()):
                tags = list(self.cars_tree.item(item, 'tags'))
                
                if 'even' in tags: tags.remove('even')
                if 'odd' in tags:  tags.remove('odd')
                
                tags.append('even' if index % 2 == 0 else 'odd')
                self.cars_tree.item(item, tags=tags)

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
            
            self._recolor_rows()

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

        for i, car in enumerate(self.cars_repo.get_all()):
            tag = 'even' if i % 2 == 0 else 'odd'
            self.cars_tree.insert('', 'end', values=astuple(car), tags=(tag,))