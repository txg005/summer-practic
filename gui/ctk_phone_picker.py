import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageDraw
from gui.theme import (BG_CARD, BG_INPUT, ACCENT, TEXT_PRI, TEXT_SEC,
                       BORDER, BTN_SEC_HVR)

COUNTRIES = [
    {
        'name': 'Беларусь',
        'code': '+375',
        'mask': '+375 (__) ___-__-__',
        'placeholder': '+375 (29) 000-00-00',
        'iso': 'BY'
    },
    {
        'name': 'Россия',
        'code': '+7',
        'mask': '+7 (___) ___-__-__',
        'placeholder': '+7 (900) 000-00-00',
        'iso': 'RU'
    },
    {
        'name': 'Казахстан',
        'code': '+7',
        'mask': '+7 (___) ___-__-__',
        'placeholder': '+7 (701) 000-00-00',
        'iso': 'KZ'
    },
    {
        'name': 'Украина',
        'code': '+380',
        'mask': '+380 (__) ___-__-__',
        'placeholder': '+380 (44) 000-00-00',
        'iso': 'UA'
    },
    {
        'name': 'Литва',
        'code': '+370',
        'mask': '+370 (__) ___-___',
        'placeholder': '+370 (60) 000-000',
        'iso': 'LT'
    },
    {
        'name': 'Латвия',
        'code': '+371',
        'mask': '+371 ____-____',
        'placeholder': '+371 2000-0000',
        'iso': 'LV'
    },
    {
        'name': 'Польша',
        'code': '+48',
        'mask': '+48 ___-___-___',
        'placeholder': '+48 123-456-789',
        'iso': 'PL'
    },
    {
        'name': 'Эстония',
        'code': '+372',
        'mask': '+372 ____-____',
        'placeholder': '+372 5000-0000',
        'iso': 'EE'
    },
]

_FLAG_CACHE = {}


def get_flag_image(iso_code: str, width=22, height=15) -> ctk.CTkImage:
    """Генерация аккуратных иконок флагов через PIL"""
    if iso_code in _FLAG_CACHE:
        return _FLAG_CACHE[iso_code]

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    w, h = width, height

    if iso_code == 'BY':
        draw.rectangle([0, 0, w, int(h * 2/3)], fill="#C8312B")
        draw.rectangle([0, int(h * 2/3), w, h], fill="#009A44")
        draw.rectangle([0, 0, int(w * 0.22), h], fill="#C8312B")
        for y in range(0, h, 3):
            draw.line([0, y, int(w * 0.22), y], fill="#FFFFFF", width=1)
    elif iso_code == 'RU':
        h3 = h / 3
        draw.rectangle([0, 0, w, h3], fill="#FFFFFF")
        draw.rectangle([0, h3, w, h3*2], fill="#0039A6")
        draw.rectangle([0, h3*2, w, h], fill="#D52B1E")
    elif iso_code == 'KZ':
        draw.rectangle([0, 0, w, h], fill="#00A2D1")
        draw.ellipse([w/2 - 3, h/2 - 3, w/2 + 3, h/2 + 3], fill="#FFC800")
    elif iso_code == 'UA':
        h2 = h / 2
        draw.rectangle([0, 0, w, h2], fill="#0057B7")
        draw.rectangle([0, h2, w, h], fill="#FFD700")
    elif iso_code == 'LT':
        h3 = h / 3
        draw.rectangle([0, 0, w, h3], fill="#FDB913")
        draw.rectangle([0, h3, w, h3*2], fill="#006A44")
        draw.rectangle([0, h3*2, w, h], fill="#C1272D")
    elif iso_code == 'LV':
        draw.rectangle([0, 0, w, int(h * 0.4)], fill="#9E3039")
        draw.rectangle([0, int(h * 0.4), w, int(h * 0.6)], fill="#FFFFFF")
        draw.rectangle([0, int(h * 0.6), w, h], fill="#9E3039")
    elif iso_code == 'PL':
        h2 = h / 2
        draw.rectangle([0, 0, w, h2], fill="#FFFFFF")
        draw.rectangle([0, h2, w, h], fill="#DC143C")
    elif iso_code == 'EE':
        h3 = h / 3
        draw.rectangle([0, 0, w, h3], fill="#0072CE")
        draw.rectangle([0, h3, w, h3*2], fill="#000000")
        draw.rectangle([0, h3*2, w, h], fill="#FFFFFF")
    else:
        draw.rectangle([0, 0, w, h], fill="#888888")

    draw.rectangle([0, 0, w - 1, h - 1], outline="#555555", width=1)

    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(width, height))
    _FLAG_CACHE[iso_code] = ctk_img
    return ctk_img


class _CountryPopup(ctk.CTkToplevel):
    """Выпадающий список выбора стран"""

    def __init__(self, master, on_select):
        super().__init__(master)
        self.overrideredirect(True)
        self.configure(fg_color=BG_CARD)
        self.attributes('-topmost', True)
        self._cb = on_select
        self._build()

    def _build(self):
        outer = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10,
                             border_width=1, border_color=BORDER)
        outer.pack(padx=1, pady=1)

        self._search_var = tk.StringVar()
        self._search_var.trace_add('write', self._filter)

        entry = ctk.CTkEntry(
            outer, textvariable=self._search_var,
            placeholder_text="🔍  Поиск страны...",
            fg_color=BG_INPUT, border_color=BORDER,
            text_color=TEXT_PRI, placeholder_text_color=TEXT_SEC,
            height=32, corner_radius=6
        )
        entry.pack(fill='x', padx=8, pady=(8, 6))

        self._list = ctk.CTkScrollableFrame(
            outer, fg_color="transparent",
            width=220,
            height=min(len(COUNTRIES), 5) * 40,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=ACCENT
        )
        self._list.pack(fill='both', expand=True, padx=4, pady=(0, 6))
        self._render(COUNTRIES)

    def _render(self, countries):
        for w in self._list.winfo_children():
            w.destroy()
        for c in countries:
            flag_img = get_flag_image(c['iso'])
            ctk.CTkButton(
                self._list,
                image=flag_img,
                text=f"  {c['name']}  ({c['code']})",
                compound='left',
                anchor='w', fg_color="transparent",
                hover_color=ACCENT, text_color=TEXT_PRI,
                height=34, corner_radius=6,
                font=ctk.CTkFont(size=12),
                command=lambda country=c: self._cb(country)
            ).pack(fill='x', pady=1)

    def _filter(self, *_):
        q = self._search_var.get().lower().strip()
        self._render([c for c in COUNTRIES
                      if q in c['name'].lower() or q in c['code']])


class CTkPhonePicker(ctk.CTkFrame):
    """Поле ввода телефона с выбором страны, флагами и динамической маской/плейсхолдером"""

    def __init__(self, master, height=34, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._country = COUNTRIES[0]
        self._digits = []
        self._is_focused = False
        self._popup = None
        self._outside_id = None

        # Кнопка выбора страны с флагом
        self._country_btn = ctk.CTkButton(
            self,
            image=get_flag_image(self._country['iso']),
            text=f"  {self._country['code']}  ▾",
            compound='left',
            width=110, height=height,
            corner_radius=6, fg_color=BG_INPUT, hover_color=BTN_SEC_HVR,
            text_color=TEXT_PRI, border_color=BORDER, border_width=1,
            command=self._toggle_popup
        )
        self._country_btn.pack(side='left', padx=(0, 6))

        # Поле ввода в стилизованной обёртке CustomTkinter
        self._entry_frame = ctk.CTkFrame(
            self, fg_color=BG_INPUT, border_color=BORDER, border_width=1,
            corner_radius=6, height=height
        )
        self._entry_frame.pack(side='left', fill='x', expand=True)
        self._entry_frame.pack_propagate(False)

        self._entry = tk.Entry(
            self._entry_frame, bg=BG_INPUT, fg=TEXT_SEC,
            insertbackground=TEXT_PRI,
            relief='flat', bd=0, font=('Segoe UI', 11),
            highlightthickness=0
        )
        self._entry.pack(fill='both', expand=True, padx=8, pady=4)

        # Обработка событий ввода и фокуса
        self._entry.bind('<KeyPress>', self._on_key)
        self._entry.bind('<FocusIn>', self._on_focus_in)
        self._entry.bind('<FocusOut>', self._on_focus_out)
        self._entry.bind('<Button-1>', self._on_click)

        self._refresh_display()

    def _max_digits(self) -> int:
        return self._country['mask'].count('_')

    def _render_mask(self) -> str:
        it = iter(self._digits)
        return ''.join(next(it, '_') if ch == '_' else ch
                       for ch in self._country['mask'])

    def _refresh_display(self):
        self._entry.delete(0, 'end')

        # Если фокус активен или уже есть введённые цифры
        if self._is_focused or len(self._digits) > 0:
            text = self._render_mask()
            # СТАЛО: белый цвет текста (или TEXT_PRI) при фокусе / вводе
            self._entry.configure(fg=TEXT_PRI)  # или TEXT_PRI
        else:
            # Исходное состояние: пример формата (плейсхолдер)
            text = self._country['placeholder']
            self._entry.configure(fg=TEXT_SEC)

        self._entry.insert(0, text)
        if self._is_focused:
            self._fix_cursor()

    def _fix_cursor(self):
        text = self._render_mask() if (self._is_focused or self._digits) else self._country['placeholder']
        pos = text.find('_')
        target = pos if pos != -1 else len(text)
        self._entry.after(1, lambda: self._entry.icursor(target))

    def _on_click(self, event=None):
        self.after(5, self._fix_cursor)

    def _on_key(self, event):
        # Пропускаем системные комбинации (например, Ctrl+C / Ctrl+A)
        if event.state & 4:
            return None

        if event.char.isdigit() and len(self._digits) < self._max_digits():
            self._digits.append(event.char)
            self._refresh_display()
        elif event.keysym == 'BackSpace' and self._digits:
            self._digits.pop()
            self._refresh_display()

        return 'break'

    def _on_focus_in(self, event=None):
        self._is_focused = True
        self._entry_frame.configure(border_color=ACCENT)
        self._refresh_display()

    def _on_focus_out(self, event=None):
        self._is_focused = False
        self._entry_frame.configure(border_color=BORDER)
        # Если номер не дописан до конца — сбрасываем ввод и возвращаем плейсхолдер
        if len(self._digits) < self._max_digits():
            self._digits = []
        self._refresh_display()

    def _toggle_popup(self):
        if self._popup and self._popup.winfo_exists():
            self._close_popup()
            return
        self._popup = _CountryPopup(self, self._on_country_select)
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        self._popup.geometry(f"+{x}+{y}")
        self.after(200, self._bind_outside)

    def _on_country_select(self, country):
        self._country = country
        self._digits = []
        self._country_btn.configure(
            image=get_flag_image(self._country['iso']),
            text=f"  {self._country['code']}  ▾"
        )
        self._close_popup()
        self._refresh_display()

    def _bind_outside(self):
        self._outside_id = self.winfo_toplevel().bind('<Button-1>', self._on_outside_click, add='+')

    def _on_outside_click(self, event):
        if not (self._popup and self._popup.winfo_exists()):
            self._unbind_outside()
            return
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
            self.winfo_toplevel().unbind('<Button-1>', self._outside_id)
        except Exception:
            pass
        self._outside_id = None

    # Public API

    def get(self) -> str:
        """Возвращает отформатированный номер, если он введён полностью, иначе пустую строку"""
        return self._render_mask() if len(self._digits) == self._max_digits() else ''

    def reset(self):
        """Сброс формы в исходное состояние"""
        self._country = COUNTRIES[0]
        self._digits = []
        self._country_btn.configure(
            image=get_flag_image(self._country['iso']),
            text=f"  {self._country['code']}  ▾"
        )
        self._refresh_display()

    def set_phone(self, value: str):
        """Загрузка номера из базы данных"""
        if not value:
            self.reset()
            return
        digits = ''.join(c for c in value if c.isdigit())
        for c in sorted(COUNTRIES, key=lambda x: len(x['code']), reverse=True):
            code_d = ''.join(ch for ch in c['code'] if ch.isdigit())
            if digits.startswith(code_d):
                self._country = c
                self._digits = list(digits[len(code_d):][:self._max_digits()])
                self._country_btn.configure(
                    image=get_flag_image(self._country['iso']),
                    text=f"  {self._country['code']}  ▾"
                )
                self._refresh_display()
                return
        self._digits = list(digits[:self._max_digits()])
        self._refresh_display()