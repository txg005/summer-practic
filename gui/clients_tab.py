import sqlite3
import tkinter as tk
from dataclasses import astuple
from tkinter import ttk, messagebox
from typing import Callable

from database import Client, ClientsRepository
from utils import validate_belarusian_phone, validate_driver_license
from utils import Tooltip


class ClientsTab:
    """Вкладка 'Клиенты' """

    def __init__(self, notebook: ttk.Notebook, clients_repo: ClientsRepository, on_clients_changed: Callable[[], None]):
        self.clients_repo = clients_repo
        self.on_clients_changed = on_clients_changed
        self.sort_column = None
        self.sort_reverse = False

        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Клиенты")

        self._create_widgets()
        self.load_clients()

    def _create_widgets(self):
        # Фрейм для формы
        form_frame = ttk.LabelFrame(self.frame, text="Добавить/Редактировать клиента")
        form_frame.pack(fill='x', padx=5, pady=5)

        # Поля формы
        ttk.Label(form_frame, text="ФИО:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.client_name = ttk.Entry(form_frame, width=30)
        self.client_name.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Водительские права:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.client_license = ttk.Entry(form_frame, width=20)
        self.client_license.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form_frame, text="Телефон:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.client_phone = ttk.Entry(form_frame, width=30)
        self.client_phone.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Email:").grid(row=1, column=2, sticky='w', padx=5, pady=5)
        self.client_email = ttk.Entry(form_frame, width=20)
        self.client_email.grid(row=1, column=3, padx=5, pady=5)
        self.client_phone.bind('<FocusIn>', self._on_phone_focus_in)
        self.client_phone.bind('<KeyRelease>', self._format_phone)

        # Кнопки
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=2, column=0, columnspan=4, pady=10)

        ttk.Button(buttons_frame, text="Добавить", command=self.add_client).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Обновить", command=self.update_client).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Удалить", command=self.delete_client).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Очистить", command=self.clear_client_form).pack(side='left', padx=5)
        _search_btn = ttk.Button(buttons_frame, text="Поиск", command=self.search_clients)
        _search_btn.pack(side='left', padx=5)
        Tooltip(_search_btn,
            "При поиске учитываются все поля:\n"
            "  • ФИО\n  • водительские права\n"
            "  • телефон\n  • email")
        ttk.Button(buttons_frame, text="Сбросить", command=self.reset_clients_search).pack(side='left', padx=5)

        # Таблица клиентов
        self.clients_tree = ttk.Treeview(
            self.frame,
            columns=('ID', 'ФИО', 'Водительские права', 'Телефон', 'Email'),
            show='headings'
        )
        self.clients_tree.pack(fill='both', expand=True, padx=5, pady=5)

        # Сортировка по заголовкам
        for col in self.clients_tree['columns']:
            self.clients_tree.heading(col, text=col, command=lambda c=col: self.sort_clients_tree(c))

        # Заголовки столбцов
        for col in self.clients_tree['columns']:
            self.clients_tree.heading(col, text=col)
            self.clients_tree.column(col, width=150)

        # Привязка событий
        self.clients_tree.bind('<ButtonRelease-1>', self.on_client_select)

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
        self.client_name.delete(0, tk.END)
        self.client_license.delete(0, tk.END)
        self.client_phone.delete(0, tk.END)
        self.client_email.delete(0, tk.END)

    def on_client_select(self, event):
        """Обработка выбора клиента"""
        selected = self.clients_tree.selection()
        if selected:
            values = self.clients_tree.item(selected[0])['values']
            self.client_name.delete(0, tk.END)
            self.client_name.insert(0, values[1])
            self.client_license.delete(0, tk.END)
            self.client_license.insert(0, values[2])
            self.client_phone.delete(0, tk.END)
            self.client_phone.insert(0, values[3])
            self.client_email.delete(0, tk.END)
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