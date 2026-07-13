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

def _make_barh_hover(fig, ax, bars, values, fmt):
    annot = ax.annotate('', xy=(0, 0), xytext=(8, 0), textcoords='offset points',
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
                annot.xy = (bar.get_width(), bar.get_y() + bar.get_height() / 2)
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

        paned = tk.PanedWindow(self.frame, orient='vertical',
                                sashwidth=14, sashrelief='flat', bg='#e0e0e0')
        paned.pack(fill='both', expand=True, padx=5, pady=5)

        text_outer = ttk.Frame(paned)
        paned.add(text_outer, minsize=80, stretch='always')
        text_scroll = ttk.Scrollbar(text_outer, orient='vertical')
        text_scroll.pack(side='right', fill='y')
        self.report_text = tk.Text(text_outer, wrap='word', yscrollcommand=text_scroll.set)
        self.report_text.pack(fill='both', expand=True)
        text_scroll.config(command=self.report_text.yview)

        self.charts_outer = ttk.Frame(paned)
        paned.add(self.charts_outer, minsize=80, stretch='always')
        self._charts_fig_canvas = None

        sash_dots = tk.Label(self.frame, text='• • •', bg='#e0e0e0',
                            fg='#888888', font=('Arial', 8), cursor='sb_v_double_arrow')

        def _place_dots(event=None):
            try:
                _, sy = paned.sash_coord(0)
                cx = paned.winfo_x() + paned.winfo_width() // 2
                cy = paned.winfo_y() + sy
                sash_dots.place(x=cx - 20, y=cy + 1, width=40, height=12)
                sash_dots.lift()
            except Exception:
                pass

        paned.bind('<Configure>', _place_dots)
        paned.bind('<ButtonRelease-1>', _place_dots)
        self.frame.after(300, _place_dots)
        
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

        monthly        = self.rentals_repo.get_income_by_month(start_date, end_date)
        monthly_booked = self.rentals_repo.get_bookings_by_month(start_date, end_date)
        by_car         = self.rentals_repo.get_income_by_car(start_date, end_date)
        booked_by_car  = self.rentals_repo.get_bookings_by_car(start_date, end_date)

        # --- месячные данные ---
        all_months         = sorted(set(r[0] for r in monthly) | set(r[0] for r in monthly_booked))
        income_m           = {r[0]: r[2] or 0 for r in monthly}
        count_m            = {r[0]: r[1]      for r in monthly}
        booked_income_m    = {r[0]: r[2] or 0 for r in monthly_booked}
        booked_count_m     = {r[0]: r[1]      for r in monthly_booked}

        m_income        = [income_m.get(m, 0)        for m in all_months]
        m_count         = [count_m.get(m, 0)         for m in all_months]
        m_booked_income = [booked_income_m.get(m, 0) for m in all_months]
        m_booked_count  = [booked_count_m.get(m, 0)  for m in all_months]

        # --- данные по автомобилям ---
        car_rows        = [r for r in by_car if (r[3] or 0) > 0]
        car_labels      = [f"{r[0]} {r[1]}" for r in car_rows]
        car_income      = [r[4] or 0         for r in car_rows]
        car_count       = [r[3] or 0         for r in car_rows]

        book_car_labels = [f"{r[0]} {r[1]}" for r in booked_by_car]
        book_car_income = [r[3] or 0         for r in booked_by_car]
        book_car_count  = [r[2] or 0         for r in booked_by_car]

        fig, axes = plt.subplots(2, 3, figsize=(16, 8))
        fig.suptitle(f'Отчёт за период {start_date} — {end_date}', fontsize=12, fontweight='bold')
        hover_cbs = []
        w = 0.35

        def no_data(ax):
            ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center',
                    transform=ax.transAxes, color='gray')

        # --- [0,0] Доходы по месяцам ---
        ax = axes[0, 0]
        if all_months:
            x  = list(range(len(all_months)))
            b1 = ax.bar([i - w/2 for i in x], m_income,        w, label='Подтверждённый',      color='steelblue')
            b2 = ax.bar([i + w/2 for i in x], m_booked_income, w, label='Потенциальный (брон.)', color='gold')
            ax.set_xticks(x); ax.set_xticklabels(all_months, rotation=45, ha='right')
            ax.legend(fontsize=8)
            hover_cbs.append(_make_bar_hover(fig, ax, list(b1)+list(b2),
                                            m_income+m_booked_income, lambda v: f'{v:.2f} BYN'))
        else:
            no_data(ax)
        ax.set_title('Доходы по месяцам'); ax.set_ylabel('BYN')

        # --- [0,1] Кол-во аренд по месяцам ---
        ax = axes[0, 1]
        if all_months:
            x  = list(range(len(all_months)))
            b3 = ax.bar([i - w/2 for i in x], m_count,        w, label='Подтверждённые', color='steelblue')
            b4 = ax.bar([i + w/2 for i in x], m_booked_count, w, label='Бронирования',   color='gold')
            ax.set_xticks(x); ax.set_xticklabels(all_months, rotation=45, ha='right')
            ax.legend(fontsize=8)
            ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
            hover_cbs.append(_make_bar_hover(fig, ax, list(b3)+list(b4),
                                            m_count+m_booked_count, lambda v: f'{int(v)} шт.'))
        else:
            no_data(ax)
        ax.set_title('Количество аренд по месяцам'); ax.set_ylabel('Кол-во')

        # --- [0,2] Доля подтверждённых vs бронирований (pie) ---
        ax = axes[0, 2]
        total_confirmed = sum(m_income)
        total_booked    = sum(m_booked_income)
        if total_confirmed > 0 or total_booked > 0:
            wedges, texts, autotexts = ax.pie(
                [total_confirmed, total_booked],
                labels=['Подтверждённый', 'Потенциальный'],
                colors=['steelblue', 'gold'],
                autopct='%1.1f%%', startangle=90
            )
            for at in autotexts:
                at.set_fontsize(9)
        else:
            no_data(ax)
        ax.set_title('Структура доходов')

        # --- [1,0] Доходы по автомобилям ---
        ax = axes[1, 0]
        if car_labels:
            b5 = ax.barh(car_labels, car_income, color='coral')
            hover_cbs.append(_make_barh_hover(fig, ax, b5, car_income, lambda v: f'{v:.2f} BYN'))
        else:
            no_data(ax)
        ax.set_title('Доходы по автомобилям (подтверждённые)'); ax.set_xlabel('BYN')

        # --- [1,1] Кол-во аренд по автомобилям ---
        ax = axes[1, 1]
        if car_labels:
            b6 = ax.barh(car_labels, car_count, color='coral')
            ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
            hover_cbs.append(_make_barh_hover(fig, ax, b6, car_count, lambda v: f'{int(v)} шт.'))
        else:
            no_data(ax)
        ax.set_title('Кол-во аренд по автомобилям'); ax.set_xlabel('Кол-во')

        # --- [1,2] Бронирования по автомобилям ---
        ax = axes[1, 2]
        if book_car_labels:
            b7 = ax.barh(book_car_labels, book_car_income, color='gold')
            hover_cbs.append(_make_barh_hover(fig, ax, b7, book_car_income, lambda v: f'{v:.2f} BYN'))
        else:
            no_data(ax)
        ax.set_title('Потенциальный доход (бронирования)'); ax.set_xlabel('BYN')

        fig.tight_layout(rect=[0, 0, 1, 0.95])

        canvas = FigureCanvasTkAgg(fig, master=self.charts_inner)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        for cb in hover_cbs:
            canvas.mpl_connect('motion_notify_event', cb)
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