import tkinter as tk
import customtkinter as ctk
from datetime import datetime, date, timedelta
from gui.theme import BG_CARD, BG_INPUT, ACCENT, TEXT_PRI, TEXT_SEC, BORDER, BTN_SEC

MONTHS_RU = ['Январь','Февраль','Март','Апрель','Май','Июнь',
             'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']
DAYS_RU   = ['Пн','Вт','Ср','Чт','Пт','Сб','Вс']


class _CalendarPopup(ctk.CTkToplevel):
    def __init__(self, master, initial: date, on_select):
        super().__init__(master)
        self.overrideredirect(True)
        self.configure(fg_color=BG_CARD)
        self.attributes('-topmost', True)
        self._cb      = on_select
        self._year    = initial.year
        self._month   = initial.month
        self._selected = initial
        self._build()
        self.after(50, self.focus_set)

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        outer = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10,
                              border_width=1, border_color=BORDER)
        outer.pack(padx=1, pady=1)

        # навигация
        nav = ctk.CTkFrame(outer, fg_color="transparent")
        nav.pack(fill='x', padx=8, pady=(8, 4))
        ctk.CTkButton(nav, text="‹", width=28, height=28,
                      fg_color=BTN_SEC, hover_color=ACCENT,
                      text_color=TEXT_PRI, corner_radius=6,
                      font=ctk.CTkFont(size=16),
                      command=self._prev).pack(side='left')
        ctk.CTkLabel(nav, text=f"{MONTHS_RU[self._month-1]} {self._year}",
                     text_color=TEXT_PRI,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side='left', expand=True)
        ctk.CTkButton(nav, text="›", width=28, height=28,
                      fg_color=BTN_SEC, hover_color=ACCENT,
                      text_color=TEXT_PRI, corner_radius=6,
                      font=ctk.CTkFont(size=16),
                      command=self._next).pack(side='right')

        # дни недели
        drow = ctk.CTkFrame(outer, fg_color="transparent")
        drow.pack(fill='x', padx=8)
        for i, d in enumerate(DAYS_RU):
            color = "#FF6B6B" if i >= 5 else TEXT_SEC
            ctk.CTkLabel(drow, text=d, text_color=color,
                         width=36, font=ctk.CTkFont(size=11)).pack(side='left')

        ctk.CTkFrame(outer, fg_color=BORDER, height=1,
                     corner_radius=0).pack(fill='x', padx=8, pady=4)

        # сетка дней
        grid = ctk.CTkFrame(outer, fg_color="transparent")
        grid.pack(padx=8, pady=(0, 8))

        today    = date.today()
        first_wd = date(self._year, self._month, 1).weekday()
        if self._month == 12:
            last_day = date(self._year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(self._year, self._month + 1, 1) - timedelta(days=1)

        day = 1
        for week in range(6):
            for wd in range(7):
                idx = week * 7 + wd
                if idx < first_wd or day > last_day.day:
                    ctk.CTkLabel(grid, text="", width=36, height=32).grid(
                        row=week, column=wd)
                    continue

                cur       = date(self._year, self._month, day)
                is_sel    = cur == self._selected
                is_today  = cur == today
                is_past   = cur < today
                is_weekend = wd >= 5

                if is_sel:
                    fg, txt = ACCENT, TEXT_PRI
                elif is_today:
                    fg, txt = "#1a4a1a", "#4CAF50"
                elif is_past:
                    fg, txt = "transparent", "#444444"
                elif is_weekend:
                    fg, txt = "transparent", "#FF8888"
                else:
                    fg, txt = "transparent", TEXT_PRI

                ctk.CTkButton(
                    grid, text=str(day), width=34, height=30,
                    fg_color=fg, hover_color=ACCENT,
                    text_color=txt, corner_radius=6,
                    font=ctk.CTkFont(size=12),
                    command=lambda d=cur: self._pick(d)
                ).grid(row=week, column=wd, padx=1, pady=1)
                day += 1

    def _pick(self, d: date):
        self._cb(d)
        self.destroy()

    def _prev(self):
        if self._month == 1: self._month = 12; self._year -= 1
        else: self._month -= 1
        self._build()

    def _next(self):
        if self._month == 12: self._month = 1; self._year += 1
        else: self._month += 1
        self._build()


class CTkDatePicker(ctk.CTkFrame):

    def __init__(self, master, height=34, **kwargs):
        super().__init__(master, fg_color="transparent")
        self._date  = datetime.today().date()
        self._popup = None

        self._entry = ctk.CTkEntry(
            self, height=height, corner_radius=6,
            fg_color=BG_INPUT, border_color=BORDER, text_color=TEXT_PRI)
        self._entry.pack(side='left', fill='x', expand=True)

        ctk.CTkButton(
            self, text="📅", width=34, height=height,
            corner_radius=6, fg_color=BTN_SEC, hover_color=ACCENT,
            text_color=TEXT_PRI, font=ctk.CTkFont(size=14),
            command=self._toggle).pack(side='left', padx=(4, 0))

        self._entry.insert(0, self._date.strftime('%Y-%m-%d'))
        self._entry.bind('<FocusOut>', self._sync)
        self._entry.bind('<Return>',   self._sync)

    def _sync(self, _=None):
        try:
            self._date = datetime.strptime(self._entry.get(), '%Y-%m-%d').date()
        except ValueError:
            self._entry.delete(0, 'end')
            self._entry.insert(0, self._date.strftime('%Y-%m-%d'))

    def _toggle(self):
        if self._popup and self._popup.winfo_exists():
            self._close_popup(); return
        self._sync()
        self._popup = _CalendarPopup(self, self._date, self._on_pick)
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        self._popup.geometry(f"+{x}+{y}")
        self.after(200, self._bind_outside_click)

    def _bind_outside_click(self):
        self._outside_bind_id = self.winfo_toplevel().bind(
            '<Button-1>', self._on_outside_click, add='+')

    def _on_outside_click(self, event):
        if not (self._popup and self._popup.winfo_exists()):
            self._unbind_outside(); return
        px, py = self._popup.winfo_rootx(), self._popup.winfo_rooty()
        pw, ph = self._popup.winfo_width(), self._popup.winfo_height()
        if not (px <= event.x_root <= px + pw and py <= event.y_root <= py + ph):
            self._close_popup()

    def _close_popup(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
        self._popup = None
        self._unbind_outside()

    def _unbind_outside(self):
        try:
            self.winfo_toplevel().unbind('<Button-1>', self._outside_bind_id)
        except Exception:
            pass
        self._outside_bind_id = None

    def _on_pick(self, d: date):
        self._date = d
        self._entry.delete(0, 'end')
        self._entry.insert(0, d.strftime('%Y-%m-%d'))
        self._popup = None
        self._unbind_outside()

    def get(self) -> str:
        self._sync()
        return self._date.strftime('%Y-%m-%d')

    def set_date(self, d):
        if isinstance(d, str):   d = datetime.strptime(d[:10], '%Y-%m-%d').date()
        elif isinstance(d, datetime): d = d.date()
        self._date = d
        self._entry.delete(0, 'end')
        self._entry.insert(0, d.strftime('%Y-%m-%d'))