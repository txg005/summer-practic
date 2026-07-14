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
                                sashwidth=14, sashrelief='flat', bg='#d0d0d0')
        paned.pack(fill='both', expand=True, padx=5, pady=5)

        # --- текстовый отчёт ---
        text_outer = ttk.Frame(paned)
        paned.add(text_outer, minsize=60, stretch='always')
        text_scroll = ttk.Scrollbar(text_outer, orient='vertical')
        text_scroll.pack(side='right', fill='y')
        self.report_text = tk.Text(text_outer, wrap='word', yscrollcommand=text_scroll.set)
        self.report_text.pack(fill='both', expand=True)
        text_scroll.config(command=self.report_text.yview)
        self.report_text.bind('<MouseWheel>',
            lambda e: self.report_text.yview_scroll(int(-1*(e.delta/120)), 'units'))

        # --- графики со скроллом ---
        charts_outer = ttk.Frame(paned)
        paned.add(charts_outer, minsize=60, stretch='always')

        charts_vscroll = ttk.Scrollbar(charts_outer, orient='vertical')
        charts_vscroll.pack(side='right', fill='y')
        self.charts_scroll_canvas = tk.Canvas(charts_outer,
                                            yscrollcommand=charts_vscroll.set)
        self.charts_scroll_canvas.pack(side='left', fill='both', expand=True)
        charts_vscroll.config(command=self.charts_scroll_canvas.yview)

        self.charts_inner = ttk.Frame(self.charts_scroll_canvas)
        self._charts_win = self.charts_scroll_canvas.create_window(
            (0, 0), window=self.charts_inner, anchor='nw')

        self.charts_inner.bind('<Configure>', lambda e:
            self.charts_scroll_canvas.configure(
                scrollregion=self.charts_scroll_canvas.bbox('all')))
        self.charts_scroll_canvas.bind('<Configure>', lambda e:
            self.charts_scroll_canvas.itemconfig(self._charts_win, width=e.width))

        def _wheel(e):
            self.charts_scroll_canvas.yview_scroll(int(-1*(e.delta/120)), 'units')
        self.charts_scroll_canvas.bind('<MouseWheel>', _wheel)
        self.charts_inner.bind('<MouseWheel>', _wheel)
        self._charts_wheel = _wheel

        # --- три точки на разделителе ---
        sash_lbl = tk.Label(self.frame, text='• • •', bg='#d0d0d0', fg='#555555',
                            font=('Arial', 8), cursor='sb_v_double_arrow')

        def _place_dots(event=None):
            try:
                _, sy = paned.sash_coord(0)
                sash_lbl.place(x=paned.winfo_x() + paned.winfo_width()//2 - 20,
                                y=paned.winfo_y() + sy + 1,
                                width=40, height=11)
                sash_lbl.lift()
            except Exception:
                pass

        paned.bind('<Configure>', _place_dots)
        paned.bind('<ButtonRelease-1>', _place_dots)
        paned.bind('<B1-Motion>', _place_dots)

        def _sash_drag(e):
            paned.sash_place(0, 0, e.y_root - paned.winfo_rooty())
            _place_dots()

        sash_lbl.bind('<B1-Motion>', _sash_drag)
        sash_lbl.bind('<ButtonRelease-1>', _place_dots)
        self.frame.after(200, _place_dots)

    def generate_report(self):
        """Генерация отчета"""
        try:
            start_date = self.report_start.get()
            end_date = self.report_end.get()

            # Очищаем поле отчета
            self.report_text.delete(1.0, tk.END)

            # Заголовок отчета
            report = f"ОТЧЕТ ПО ДОХОДАМ\n"
            report += f"Период: с {start_date} 00:00 по {end_date} 23:59\n"
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

        for w in self.charts_inner.winfo_children():
            w.destroy()

        monthly       = self.rentals_repo.get_income_by_month(start_date, end_date)
        by_car        = self.rentals_repo.get_income_by_car(start_date, end_date)
        monthly_book  = self.rentals_repo.get_bookings_by_month()
        booked_by_car = self.rentals_repo.get_bookings_by_car()

        months   = [r[0] for r in monthly]
        m_income = [r[2] or 0 for r in monthly]
        m_count  = [r[1] for r in monthly]
        bk_months  = [r[0] for r in monthly_book]
        bk_income  = [r[2] or 0 for r in monthly_book]
        bk_count   = [r[1] for r in monthly_book]

        def trunc(s): return s[:18] + '…' if len(s) > 18 else s

        car_rows   = [r for r in by_car if (r[4] or 0) > 0]
        car_labels = [trunc(f"{r[0]} {r[1]}") for r in car_rows]
        car_income = [r[4] or 0 for r in car_rows]
        car_count  = [r[3] or 0 for r in car_rows]

        bc_labels = [trunc(f"{r[0]} {r[1]}") for r in booked_by_car]
        bc_income = [r[3] or 0 for r in booked_by_car]
        bc_count  = [r[2] or 0 for r in booked_by_car]

        n_cars = max(len(car_labels), len(bc_labels), 4)
        row_h  = max(2.0, n_cars * 0.22)
        fig_h  = min(row_h * 3 + 1.0, 15.0)

        fig, axes = plt.subplots(3, 2, figsize=(14, fig_h))
        fig.suptitle(f'Отчёт {start_date} 00:00 — {end_date} 23:59', fontsize=11, fontweight='bold')
        fig.subplots_adjust(left=0.22, right=0.97, top=0.97, bottom=0.08,
                            hspace=0.55, wspace=0.45)

        def no_data(ax, title):
            ax.set_title(title, fontsize=9, pad=6)
            ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center',
                    transform=ax.transAxes, color='gray', fontsize=9)
            ax.axis('off')

        def bar_hover(ax, bars, vals, fmt):
            ann = ax.annotate('', xy=(0,0), xytext=(0, -28),
                            textcoords='offset points',
                            bbox=dict(boxstyle='round,pad=0.3', fc='white',
                                        ec='gray', alpha=0.92),
                            fontsize=8, visible=False, zorder=10)
            def on_hover(event):
                if event.inaxes != ax:
                    if ann.get_visible(): ann.set_visible(False); fig.canvas.draw_idle()
                    return
                for b, v in zip(bars, vals):
                    if b.contains(event)[0]:
                        ann.xy = (b.get_x() + b.get_width()/2, b.get_height())
                        ann.set_text(fmt(v)); ann.set_visible(True)
                        fig.canvas.draw_idle(); return
                if ann.get_visible(): ann.set_visible(False); fig.canvas.draw_idle()
            return on_hover

        def barh_hover(ax, bars, vals, fmt):
            ann = ax.annotate('', xy=(0,0), xytext=(6, 0),
                            textcoords='offset points',
                            bbox=dict(boxstyle='round,pad=0.3', fc='white',
                                        ec='gray', alpha=0.92),
                            fontsize=8, visible=False, zorder=10)
            def on_hover(event):
                if event.inaxes != ax:
                    if ann.get_visible(): ann.set_visible(False); fig.canvas.draw_idle()
                    return
                for b, v in zip(bars, vals):
                    if b.contains(event)[0]:
                        ann.xy = (b.get_width(), b.get_y() + b.get_height()/2)
                        ann.set_text(fmt(v)); ann.set_visible(True)
                        fig.canvas.draw_idle(); return
                if ann.get_visible(): ann.set_visible(False); fig.canvas.draw_idle()
            return on_hover

        cbs = []
        fmt_byn   = lambda v: f'{v:.2f} BYN'
        fmt_count = lambda v: f'{int(v)} шт.'

        # [0,0] Доходы по месяцам
        ax = axes[0, 0]
        if months:
            b = ax.bar(months, m_income, color='steelblue', width=0.5)
            ax.set_ylabel('BYN', fontsize=8)
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right', fontsize=8)
            cbs.append(bar_hover(ax, b, m_income, fmt_byn))
        else:
            no_data(ax, 'Доходы по месяцам'); ax = None
        if ax: ax.set_title('Доходы по месяцам', fontsize=9, pad=6); ax.tick_params(labelsize=8)

        # [0,1] Кол-во аренд по месяцам
        ax = axes[0, 1]
        if months:
            b = ax.bar(months, m_count, color='steelblue', width=0.5)
            ax.set_ylabel('Кол-во', fontsize=8)
            ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right', fontsize=8)
            cbs.append(bar_hover(ax, b, m_count, fmt_count))
        else:
            no_data(ax, 'Кол-во аренд по месяцам'); ax = None
        if ax: ax.set_title('Кол-во аренд по месяцам', fontsize=9, pad=6); ax.tick_params(labelsize=8)

        # [1,0] Доходы по автомобилям
        ax = axes[1, 0]
        if car_labels:
            b = ax.barh(car_labels, car_income, color='coral', height=0.6)
            ax.set_xlabel('BYN', fontsize=8)
            ax.tick_params(labelsize=8)
            cbs.append(barh_hover(ax, b, car_income, fmt_byn))
        else:
            no_data(ax, 'Доходы по автомобилям')
        ax.set_title('Доходы по автомобилям', fontsize=9, pad=6)

        # [1,1] Кол-во аренд по автомобилям
        ax = axes[1, 1]
        if car_labels:
            b = ax.barh(car_labels, car_count, color='coral', height=0.6)
            ax.set_xlabel('Кол-во', fontsize=8)
            ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
            ax.tick_params(labelsize=8)
            cbs.append(barh_hover(ax, b, car_count, fmt_count))
        else:
            no_data(ax, 'Кол-во аренд по автомобилям')
        ax.set_title('Кол-во аренд по автомобилям', fontsize=9, pad=6)

        # [2,0] Потенциальный доход по месяцам
        ax = axes[2, 0]
        if bk_months:
            b = ax.bar(bk_months, bk_income, color='gold', width=0.5)
            ax.set_ylabel('BYN', fontsize=8)
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right', fontsize=8)
            cbs.append(bar_hover(ax, b, bk_income, fmt_byn))
        else:
            no_data(ax, 'Бронирования по месяцам'); ax = None
        if ax: ax.set_title('Бронирования по месяцам', fontsize=9, pad=6); ax.tick_params(labelsize=8)

        # [2,1] Потенциальный доход по автомобилям
        ax = axes[2, 1]
        if bc_labels:
            b = ax.barh(bc_labels, bc_income, color='gold', height=0.6)
            ax.set_xlabel('BYN', fontsize=8)
            ax.tick_params(labelsize=8)
            cbs.append(barh_hover(ax, b, bc_income, fmt_byn))
        else:
            no_data(ax, 'Бронирования по автомобилям')
        ax.set_title('Бронирования по автомобилям', fontsize=9, pad=6)

        canvas = FigureCanvasTkAgg(fig, master=self.charts_inner)
        canvas.draw()
        mpl_widget = canvas.get_tk_widget()
        mpl_widget.pack(fill='both', expand=True)
        mpl_widget.bind('<MouseWheel>', self._charts_wheel)

        for cb in cbs:
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