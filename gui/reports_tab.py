import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk, messagebox, filedialog

from database import RentalsRepository


class ReportsTab:
    """Вкладка 'Отчеты' """

    def __init__(self, notebook: ttk.Notebook, rentals_repo: RentalsRepository):
        self.rentals_repo = rentals_repo

        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Отчеты")

        self._create_widgets()

    def _create_widgets(self):
        # Фрейм для параметров отчета
        params_frame = ttk.LabelFrame(self.frame, text="Параметры отчета")
        params_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(params_frame, text="Дата начала:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.report_start = ttk.Entry(params_frame, width=15)
        self.report_start.grid(row=0, column=1, padx=5, pady=5)
        self.report_start.insert(0, (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))

        ttk.Label(params_frame, text="Дата окончания:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.report_end = ttk.Entry(params_frame, width=15)
        self.report_end.grid(row=0, column=3, padx=5, pady=5)
        self.report_end.insert(0, datetime.now().strftime('%Y-%m-%d'))

        ttk.Button(params_frame, text="Сформировать отчет", command=self.generate_report).grid(
            row=0, column=4, padx=5, pady=5)
        ttk.Button(params_frame, text="Экспорт в Excel", command=self.export_to_excel).grid(
            row=0, column=5, padx=5, pady=5)

        # Текстовое поле для отчета
        self.report_text = tk.Text(self.frame, height=25, width=100)
        self.report_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Скроллбар для отчета
        report_scrollbar = ttk.Scrollbar(self.frame, orient='vertical', command=self.report_text.yview)
        report_scrollbar.pack(side='right', fill='y')
        self.report_text.configure(yscrollcommand=report_scrollbar.set)

    def generate_report(self):
        """Генерация отчета"""
        try:
            start_date = self.report_start.get()
            end_date = self.report_end.get()

            # Очищаем поле отчета
            self.report_text.delete(1.0, tk.END)

            # Заголовок отчета
            report = f"ОТЧЕТ ПО ДОХОДАМ\n"
            report += f"Период: с {start_date} по {end_date}\n"
            report += "=" * 60 + "\n\n"

            # Общая статистика
            total_rentals, total_income = self.rentals_repo.get_income_summary(start_date, end_date)
            report += f"Общая статистика:\n"
            report += f"Количество аренд: {total_rentals}\n"
            report += f"Общий доход: {total_income:.2f} BYN\n\n"

            # Детализация по автомобилям
            report += "Доходы по автомобилям:\n"
            report += "-" * 60 + "\n"
            for brand, model, plate, count, income in self.rentals_repo.get_income_by_car(start_date, end_date):
                report += f"{brand} {model} ({plate}): {count} аренд, {income or 0:.2f} BYN\n"

            report += "\n" + "-" * 60 + "\n"

            # Статистика по месяцам
            report += "\nДоходы по месяцам:\n"
            report += "-" * 30 + "\n"
            for month, count, income in self.rentals_repo.get_income_by_month(start_date, end_date):
                report += f"{month}: {count} аренд, {income:.2f} BYN\n"

            # Активные аренды
            active_rentals = self.rentals_repo.get_active_rentals()
            if active_rentals:
                report += f"\nАктивные аренды ({len(active_rentals)}):\n"
                report += "-" * 60 + "\n"
                for brand, model, client, start, end in active_rentals:
                    report += f"{brand} {model} - {client} ({start} - {end})\n"

            # Просроченные аренды (уведомления)
            today = datetime.now().strftime('%Y-%m-%d %H:%M')
            overdue_rentals = self.rentals_repo.get_overdue_rentals(today)
            if overdue_rentals:
                report += f"\n⚠️ ПРОСРОЧЕННЫЕ АРЕНДЫ ({len(overdue_rentals)}):\n"
                report += "-" * 60 + "\n"
                for brand, model, client, phone, end_date in overdue_rentals:
                    days_overdue = (datetime.now() - datetime.strptime(end_date, '%Y-%m-%d')).days
                    report += f"{brand} {model} - {client} ({phone})\n"
                    report += f"  Просрочено на {days_overdue} дней (до {end_date})\n\n"

            self.report_text.insert(1.0, report)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при формировании отчета: {str(e)}")

    def export_to_excel(self):
        """Экспорт в XLSX"""
        try:
            from openpyxl import Workbook

            # Получаем данные
            start_date = self.report_start.get()
            end_date = self.report_end.get()
            data = self.rentals_repo.get_export_data(start_date, end_date)

            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"отчёт по доходам с {start_date} по {end_date}"
            )
            if not filename:
                return

            # Создаём Excel-файл
            wb = Workbook()
            ws = wb.active
            ws.title = "Аренды"

            # Заголовки
            headers = ['ID', 'Марка', 'Модель', 'Номер', 'Клиент',
                       'Телефон', 'Начало', 'Окончание', 'Стоимость', 'Статус']
            ws.append(headers)

            # Данные
            for row in data:
                ws.append(row)

            # Автоподбор ширины столбцов
            for col in ws.columns:
                max_length = max((len(str(cell.value)) for cell in col if cell.value), default=0)
                ws.column_dimensions[col[0].column_letter].width = (max_length + 2) * 1.2

            wb.save(filename)
            messagebox.showinfo("Успех", f"Отчёт сохранён в {filename}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать: {str(e)}")