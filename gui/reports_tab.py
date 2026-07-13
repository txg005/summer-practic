import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk, messagebox, filedialog

from database import RentalsRepository


def _make_bar_hover(fig, ax, bars, values, fmt):
    annot = ax.annotate('', xy=(0, 0), xytext=(8, 8), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='gray', alpha=0.9),
                        fontsize=9, visible=False)
    def on_hover(event):
        if event.inaxes != ax:
            if annot.get_visible():
                annot.set_visible(False)
                fig.canvas.draw_idle()
            return
        for bar, val in zip(bars, values):
            if bar.contains(event)[0]:
                annot.xy = (bar.get_x() + bar.get_width() / 2, bar.get_height())
                annot.set_text(fmt(val))
                annot.set_visible(True)
                fig.canvas.draw_idle()
                return
        if annot.get_visible():
            annot.set_visible(False)
            fig.canvas.draw_idle()
    return on_hover


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

        paned = ttk.PanedWindow(self.frame, orient='vertical')
        paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # --- верхняя панель: текстовый отчёт ---
        text_outer = ttk.Frame(paned)
        paned.add(text_outer, weight=1)

        text_scroll = ttk.Scrollbar(text_outer, orient='vertical')
        text_scroll.pack(side='right', fill='y')
        self.report_text = tk.Text(text_outer, wrap='word', yscrollcommand=text_scroll.set)
        self.report_text.pack(fill='both', expand=True)
        text_scroll.config(command=self.report_text.yview)

        # --- нижняя панель: графики со скроллом ---
        charts_outer = ttk.Frame(paned)
        paned.add(charts_outer, weight=1)

        charts_vscroll = ttk.Scrollbar(charts_outer, orient='vertical')
        charts_vscroll.pack(side='right', fill='y')
        self.charts_canvas = tk.Canvas(charts_outer, yscrollcommand=charts_vscroll.set)
        self.charts_canvas.pack(fill='both', expand=True)
        charts_vscroll.config(command=self.charts_canvas.yview)

        self.charts_inner = ttk.Frame(self.charts_canvas)
        self.charts_canvas.create_window((0, 0), window=self.charts_inner, anchor='nw')
        self.charts_inner.bind('<Configure>', lambda e: self.charts_canvas.configure(
            scrollregion=self.charts_canvas.bbox('all')))

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
            booked_count, booked_potential = self.rentals_repo.get_bookings_summary(start_date, end_date)

            report += f"Подтверждённые аренды:\n"
            report += f"Количество: {total_rentals}, доход: {total_income:.2f} BYN\n\n"
            report += f"Бронирования (доход ещё не получен, могут быть отменены):\n"
            report += f"Количество: {booked_count}, потенциальный доход: {booked_potential:.2f} BYN\n\n"
            
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
                    days_overdue = (datetime.now() - datetime.strptime(end_date, '%Y-%m-%d %H:%M')).days
                    report += f"{brand} {model} - {client} ({phone})\n"
                    report += f"  Просрочено на {days_overdue} дней (до {end_date})\n\n"

            # Секция бронирований и вызов графиков
            booked_list = self.rentals_repo.get_booked_rentals(start_date, end_date)
            if booked_list:
                report += f"\nЗабронированные аренды ({len(booked_list)}):\n"
                report += "-" * 60 + "\n"
                for brand, model, client, start, end, cost in booked_list:
                    report += f"{brand} {model} — {client}: {start} → {end}, {cost:.2f} BYN\n"

            self.report_text.insert(1.0, report)
            self._show_charts(start_date, end_date)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при формировании отчета: {str(e)}")

    def _show_charts(self, start_date: str, end_date: str):
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except ImportError:
            return

        for widget in self.charts_inner.winfo_children():
            widget.destroy()

        monthly = self.rentals_repo.get_income_by_month(start_date, end_date)
        monthly_booked = self.rentals_repo.get_bookings_by_month(start_date, end_date)
        by_car = self.rentals_repo.get_income_by_car(start_date, end_date)

        # Объединяем месяцы из дохода и бронирований
        all_months = sorted(set(r[0] for r in monthly) | set(r[0] for r in monthly_booked))
        income_by_month = {r[0]: (r[2] or 0) for r in monthly}
        booked_by_month = {r[0]: (r[2] or 0) for r in monthly_booked}
        month_income = [income_by_month.get(m, 0) for m in all_months]
        month_booked = [booked_by_month.get(m, 0) for m in all_months]

        car_labels = [f"{r[0]} {r[1]}" for r in by_car if r[4] and r[4] > 0]
        car_income = [r[4] for r in by_car if r[4] and r[4] > 0]

        has_monthly = bool(all_months)
        has_cars = bool(car_income)
        n = sum([has_monthly, has_cars])
        if n == 0:
            return

        fig, axes = plt.subplots(1, n, figsize=(6 * n, 4))
        if n == 1:
            axes = [axes]

        idx = 0
        if has_monthly:
            x = range(len(all_months))
            width = 0.4
            axes[idx].bar([i - width/2 for i in x], month_income, width, label='Доход', color='steelblue')
            axes[idx].bar([i + width/2 for i in x], month_booked, width, label='Бронирования', color='gold')
            axes[idx].set_title('Доходы по месяцам')
            axes[idx].set_ylabel('BYN')
            axes[idx].set_xticks(list(x))
            axes[idx].set_xticklabels(all_months, rotation=45, ha='right')
            axes[idx].legend()
            idx += 1

        if has_cars:
            axes[idx].barh(car_labels, car_income, color='coral')
            axes[idx].set_title('Доходы по автомобилям')
            axes[idx].set_xlabel('BYN')

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.charts_inner)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        plt.close(fig)

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