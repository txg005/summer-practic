import sqlite3
import tkinter as tk
from dataclasses import astuple
from tkinter import ttk, messagebox
from typing import Callable
import customtkinter as ctk
from gui.theme import (BG_MAIN, BG_CARD, BG_INPUT, ACCENT, ACCENT_HOVER,
                       TEXT_PRI, TEXT_SEC, BORDER, BTN_SEC, BTN_SEC_HVR,
                       BTN_DEL, BTN_DEL_HVR)

from database import Client, ClientsRepository
from utils import validate_belarusian_phone, validate_driver_license
from utils import Tooltip


class ClientsTab:
    """Вкладка 'Клиенты' """

    def __init__(self, parent_frame, clients_repo: ClientsRepository, on_clients_changed: Callable[[], None]):
        self.clients_repo = clients_repo
        self.on_clients_changed = on_clients_changed
        self.sort_column = None
        self.sort_reverse = False

        self.frame = tk.Frame(parent_frame, bg=BG_MAIN)
        self.frame.pack(fill='both', expand=True)

        self._create_widgets()
        self.load_clients()

    def _create_widgets(self):
        entry_kw = dict(fg_color=BG_INPUT, border_color=BORDER,
                        text_color=TEXT_PRI, placeholder_text_color=TEXT_SEC,
                        height=34, corner_radius=6)
        btn_pri = dict(height=34, corner_radius=8,
                    fg_color=ACCENT,  hover_color=ACCENT_HOVER)
        btn_sec = dict(height=34, corner_radius=8,
                    fg_color=BTN_SEC, hover_color=BTN_SEC_HVR, text_color=TEXT_PRI)
        btn_del = dict(height=34, corner_radius=8,
                    fg_color=BTN_DEL, hover_color=BTN_DEL_HVR, text_color=TEXT_PRI)

        def field(parent, label_text, col, padleft=0, padright=0):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=0, column=col, sticky='ew',
                padx=(padleft, padright), pady=2)
            ctk.CTkLabel(f, text=label_text, text_color=TEXT_SEC,
                        font=ctk.CTkFont(size=12)).pack(anchor='w', pady=(4, 2))
            return f

        # Карточка формы
        card = ctk.CTkFrame(self.frame, fg_color=BG_CARD, corner_radius=12)
        card.pack(fill='x', padx=16, pady=(12, 6))

        # заголовок
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill='x', padx=16, pady=(12, 0))
        ctk.CTkLabel(hdr, text="Клиент",
                    text_color=TEXT_PRI,
                    font=ctk.CTkFont(size=14, weight="bold")).pack(side='left')
        ctk.CTkButton(hdr, text="Сбросить", width=90,
                    command=self.reset_clients_search, **btn_sec).pack(side='right', padx=(4, 0))
        _sb = ctk.CTkButton(hdr, text="Поиск", width=90,
                            command=self.search_clients, **btn_pri)
        _sb.pack(side='right', padx=(4, 4))
        Tooltip(_sb,
                "При поиске учитываются все поля:\n"
                "  • ФИО\n  • водительские права\n"
                "  • телефон\n  • email")

        ctk.CTkFrame(card, fg_color=BORDER, height=1,
                    corner_radius=0).pack(fill='x', padx=16, pady=8)

        # поля — строка 1
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill='x', padx=16)
        row1.columnconfigure((0, 1), weight=1)

        f = field(row1, "ФИО", 0, padright=6)
        self.client_name = ctk.CTkEntry(f, placeholder_text="Иванов Иван Иванович", **entry_kw)
        self.client_name.pack(fill='x')

        f = field(row1, "Водительские права", 1, padleft=6)
        self.client_license = ctk.CTkEntry(f, placeholder_text="5JK 789012", **entry_kw)
        self.client_license.pack(fill='x')

        # поля — строка 2
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill='x', padx=16, pady=(0, 4))
        row2.columnconfigure((0, 1), weight=1)

        f = field(row2, "Телефон", 0, padright=6)
        self.client_phone = ctk.CTkEntry(f, placeholder_text="+375 29 000-00-00", **entry_kw)
        self.client_phone.pack(fill='x')
        self.client_phone.bind('<FocusIn>',   self._on_phone_focus_in)
        self.client_phone.bind('<KeyRelease>', self._format_phone)

        f = field(row2, "Email", 1, padleft=6)
        self.client_email = ctk.CTkEntry(f, placeholder_text="example@mail.com", **entry_kw)
        self.client_email.pack(fill='x')

        # кнопки CRUD
        ctk.CTkFrame(card, fg_color=BORDER, height=1,
                    corner_radius=0).pack(fill='x', padx=16, pady=(6, 8))
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(padx=16, pady=(0, 12), anchor='w')

        ctk.CTkButton(btns, text="Добавить", width=110, command=self.add_client,       **btn_pri).pack(side='left', padx=(0, 6))
        ctk.CTkButton(btns, text="Обновить", width=110, command=self.update_client,     **btn_sec).pack(side='left', padx=6)
        ctk.CTkButton(btns, text="Удалить",  width=110, command=self.delete_client,     **btn_del).pack(side='left', padx=6)
        ctk.CTkButton(btns, text="Очистить", width=110, command=self.clear_client_form, **btn_sec).pack(side='left', padx=6)

        # Таблица
        tree_card = ctk.CTkFrame(self.frame, fg_color=BG_CARD, corner_radius=12)
        tree_card.pack(fill='both', expand=True, padx=16, pady=(0, 12))

        tree_wrap = tk.Frame(tree_card, bg=BG_CARD)
        tree_wrap.pack(fill='both', expand=True, padx=8, pady=8)

        cols = ('ID', 'ФИО', 'Водительские права', 'Телефон', 'Email')
        self.clients_tree = ttk.Treeview(tree_wrap, columns=cols, show='headings')
        self.clients_tree.pack(fill='both', expand=True, side='left')

        widths = {'ID': 45, 'Водительские права': 140, 'Телефон': 150}
        for col in cols:
            self.clients_tree.heading(col, text=col,
                                    command=lambda c=col: self.sort_clients_tree(c))
            self.clients_tree.column(col, width=widths.get(col, 200), minwidth=50)

        sb = ttk.Scrollbar(tree_wrap, orient='vertical', command=self.clients_tree.yview)
        sb.pack(side='right', fill='y')
        self.clients_tree.configure(yscrollcommand=sb.set)
        self.clients_tree.bind('<ButtonRelease-1>', self.on_client_select)
        self.clients_tree.bind('<MouseWheel>', lambda e:
            self.clients_tree.yview_scroll(int(-1*(e.delta/120)), 'units'))

    def add_client(self):
        """Добавление клиента"""
        try:
            name = self.client_name.get().strip()
            license_num = self.client_license.get().strip()
            phone = self.client_phone.get().strip()
            email = self.client_email.get().strip()

            # Валидация
            if not all([name, license_num, phone, email]):
                messagebox.showerror("Ошибка", "Все поля должны быть заполнены!")
                return

            if not validate_belarusian_phone(phone):
                messagebox.showerror("Ошибка", "Неверный формат телефона! Пример: +375 29 123-45-67")
                return

            if not validate_driver_license(license_num):
                messagebox.showerror("Ошибка", "Неверный формат водительских прав! Пример: 1AB 123456")
                return

            if '@' not in email or '.' not in email:
                messagebox.showerror("Ошибка", "Неверный формат email!")
                return

            self.clients_repo.insert(Client(full_name=name, driver_license=license_num,
                                            phone=phone, email=email))
            self.load_clients()
            self.on_clients_changed()
            self.clear_client_form()
            messagebox.showinfo("Успех", "Клиент добавлен!")

        except sqlite3.IntegrityError:
            messagebox.showerror("Ошибка", "Клиент с такими водительскими правами уже существует!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при добавлении: {str(e)}")

    def update_client(self):
        """Обновление клиента"""
        selected = self.clients_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите клиента для обновления!")
            return

        try:
            client_id = self.clients_tree.item(selected[0])['values'][0]
            name = self.client_name.get().strip()
            license_num = self.client_license.get().strip()
            phone = self.client_phone.get().strip()
            email = self.client_email.get().strip()

            # Валидация
            if not all([name, license_num, phone, email]):
                messagebox.showerror("Ошибка", "Все поля должны быть заполнены!")
                return

            if not validate_belarusian_phone(phone):
                messagebox.showerror("Ошибка", "Неверный формат телефона! Пример: +375 29 123-45-67")
                return

            if not validate_driver_license(license_num):
                messagebox.showerror("Ошибка", "Неверный формат водительских прав! Пример: 1AB 123456")
                return

            self.clients_repo.update(Client(id=client_id, full_name=name, driver_license=license_num,
                                            phone=phone, email=email))
            self.load_clients()
            self.on_clients_changed()
            messagebox.showinfo("Успех", "Клиент обновлен!")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при обновлении: {str(e)}")

    def delete_client(self):
        """Удаление клиента"""
        selected = self.clients_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите клиента для удаления!")
            return

        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить клиента?"):
            try:
                client_id = self.clients_tree.item(selected[0])['values'][0]
                self.clients_repo.delete(client_id)
                self.load_clients()
                self.on_clients_changed()
                self.clear_client_form()
                messagebox.showinfo("Успех", "Клиент удален!")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при удалении: {str(e)}")

    def clear_client_form(self):
        """Очистка формы клиента"""
        self.client_name.delete(0, 'end')
        self.client_license.delete(0, 'end')
        self.client_phone.delete(0, 'end')
        self.client_email.delete(0, 'end')

    def on_client_select(self, event):
        """Обработка выбора клиента"""
        selected = self.clients_tree.selection()
        if selected:
            values = self.clients_tree.item(selected[0])['values']
            self.client_name.delete(0, 'end')
            self.client_name.insert(0, values[1])
            self.client_license.delete(0, 'end')
            self.client_license.insert(0, values[2])
            self.client_phone.delete(0, 'end')
            self.client_phone.insert(0, values[3])
            self.client_email.delete(0, 'end')
            self.client_email.insert(0, values[4])

    def sort_clients_tree(self, col):
        """Сортировка таблицы клиентов с реверсом"""
        # Определяем направление сортировки
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
        self.sort_column = col

        # Собираем данные для сортировки
        data = [(self.clients_tree.set(child, col), child) for child in self.clients_tree.get_children('')]

        # Сортируем данные с учетом направления
        try:
            if col == 'ID':
                data.sort(key=lambda x: int(x[0]) if x[0] else 0, reverse=self.sort_reverse)
            else:
                data.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)
        except (ValueError, TypeError):
            data.sort(key=lambda x: str(x[0]).lower(), reverse=self.sort_reverse)

        # Перемещаем строки в отсортированном порядке
        for index, (val, child) in enumerate(data):
            self.clients_tree.move(child, '', index)

        # Обновляем заголовки для визуального отображения сортировки
        for c in self.clients_tree['columns']:
            text = self.clients_tree.heading(c, 'text').replace(' ▲', '').replace(' ▼', '')
            if c == col:
                text += ' ▼' if self.sort_reverse else ' ▲'
            self.clients_tree.heading(c, text=text)

    def search_clients(self):
        """Поиск клиентов"""
        name = self.client_name.get().strip()
        license_num = self.client_license.get().strip()
        phone = self.client_phone.get().strip()
        email = self.client_email.get().strip()

        try:
            clients = self.clients_repo.search(name=name, license_num=license_num,
                                               phone=phone, email=email)
            for item in self.clients_tree.get_children():
                self.clients_tree.delete(item)
            for client in clients:
                self.clients_tree.insert('', 'end', values=astuple(client))

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка поиска: {str(e)}")
            self.load_clients()

    def reset_clients_search(self):
        """Сброс поиска клиентов"""
        self.load_clients()
        for c in self.clients_tree['columns']:
            text = self.clients_tree.heading(c, 'text').replace(' ▲', '').replace(' ▼', '')
            self.clients_tree.heading(c, text=text)

    def load_clients(self):
        """Загрузка списка клиентов"""
        for item in self.clients_tree.get_children():
            self.clients_tree.delete(item)
        for client in self.clients_repo.get_all():
            self.clients_tree.insert('', 'end', values=astuple(client))

    def _on_phone_focus_in(self, event):
        if not self.client_phone.get():
            self.client_phone.insert(0, '+375 ')

    def _format_phone(self, event):
        if event.keysym in ('Tab', 'Return', 'Escape', 'Left', 'Right',
                            'Home', 'End', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R'):
            return
        digits = ''.join(c for c in self.client_phone.get() if c.isdigit())
        if digits.startswith('375'):
            digits = digits[3:]
        digits = digits[:9]
        result = '+375'
        if digits:        result += ' ' + digits[:2]
        if len(digits) > 2: result += ' ' + digits[2:5]
        if len(digits) > 5: result += '-' + digits[5:7]
        if len(digits) > 7: result += '-' + digits[7:9]
        self.client_phone.delete(0, tk.END)
        self.client_phone.insert(0, result)
        self.client_phone.icursor(len(result))