"""Централизованная тёмная тема приложения.

Цветовая схема:
- bg_primary:    #0f0f1a  — фон окна
- bg_secondary:  #1a1a2e  — фон панелей, карточек
- bg_tertiary:   #252540  — поля ввода, hover
- accent:        #e94560  — кнопки, активные элементы
- accent_hover:  #ff6b81  — hover кнопок
- text_primary:  #ffffff  — основной текст
- text_secondary:#a0a0b8  — вторичный текст, placeholder
- border:        #2a2a45  — границы
- success:       #2ecc71  — успех
- warning:       #f39c12  — предупреждение
"""

# ── Цвета ───────────────────────────────────────────────
BG_PRIMARY    = "#0f0f1a"
BG_SECONDARY  = "#1a1a2e"
BG_TERTIARY   = "#252540"
ACCENT        = "#e94560"
ACCENT_HOVER  = "#ff6b81"
TEXT_PRIMARY  = "#ffffff"
TEXT_SECONDARY = "#a0a0b8"
BORDER        = "#2a2a45"
SUCCESS       = "#2ecc71"
WARNING       = "#f39c12"

# ── Шрифты ──────────────────────────────────────────────
FONT_FAMILY = "Segoe UI"
FONT_SIZE_SMALL  = 10
FONT_SIZE_NORMAL = 11
FONT_SIZE_LARGE  = 14
FONT_SIZE_TITLE  = 18

FONTS = {
    "small":  (FONT_FAMILY, FONT_SIZE_SMALL),
    "normal": (FONT_FAMILY, FONT_SIZE_NORMAL),
    "large":  (FONT_FAMILY, FONT_SIZE_LARGE),
    "title":  (FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
    "bold":   (FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
}


def apply_theme(root):
    """Применить тёмную тему ко всему приложению."""
    style = __import__("tkinter").ttk.Style()

    # Общие настройки
    root.configure(bg=BG_PRIMARY)
    style.theme_use("clam")

    # ── Frame ─────────────────────────────────────────────
    style.configure(
        "TFrame",
        background=BG_PRIMARY,
    )

    # ── Label ─────────────────────────────────────────────
    style.configure(
        "TLabel",
        background=BG_PRIMARY,
        foreground=TEXT_PRIMARY,
        font=FONTS["normal"],
    )

    # ── Entry ─────────────────────────────────────────────
    style.configure(
        "TEntry",
        fieldbackground=BG_TERTIARY,
        foreground=TEXT_PRIMARY,
        insertcolor=TEXT_PRIMARY,
        borderwidth=1,
        relief="flat",
    )
    style.map(
        "TEntry",
        fieldbackground=[("focus", BG_TERTIARY)],
        bordercolor=[("focus", ACCENT)],
    )

    # ── Combobox ──────────────────────────────────────────
    style.configure(
        "TCombobox",
        fieldbackground=BG_TERTIARY,
        foreground=TEXT_PRIMARY,
        background=BG_TERTIARY,
        arrowcolor=TEXT_PRIMARY,
        borderwidth=1,
        relief="flat",
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", BG_TERTIARY), ("active", BG_TERTIARY)],
        selectbackground=[("readonly", ACCENT)],
    )

    # ── Button (основной) ─────────────────────────────────
    style.configure(
        "Accent.TButton",
        background=ACCENT,
        foreground=TEXT_PRIMARY,
        font=FONTS["bold"],
        borderwidth=0,
        focusthickness=0,
        padding=(12, 6),
    )
    style.map(
        "Accent.TButton",
        background=[("active", ACCENT_HOVER), ("pressed", "#c73e54")],
        foreground=[("active", TEXT_PRIMARY)],
    )

    # ── Button (вторичный) ────────────────────────────────
    style.configure(
        "Secondary.TButton",
        background=BG_TERTIARY,
        foreground=TEXT_PRIMARY,
        font=FONTS["normal"],
        borderwidth=0,
        focusthickness=0,
        padding=(10, 4),
    )
    style.map(
        "Secondary.TButton",
        background=[("active", "#303055")],
        foreground=[("active", TEXT_PRIMARY)],
    )

    # ── Treeview (таблица) ────────────────────────────────
    style.configure(
        "Custom.Treeview",
        background=BG_SECONDARY,
        foreground=TEXT_PRIMARY,
        fieldbackground=BG_SECONDARY,
        borderwidth=0,
        relief="flat",
        rowheight=32,
        font=FONTS["normal"],
    )
    style.configure(
        "Custom.Treeview.Heading",
        background=BG_TERTIARY,
        foreground=TEXT_PRIMARY,
        font=FONTS["bold"],
        borderwidth=0,
        relief="flat",
        padding=(8, 6),
    )
    style.map(
        "Custom.Treeview",
        background=[("selected", ACCENT)],
        foreground=[("selected", TEXT_PRIMARY)],
    )
    style.map(
        "Custom.Treeview.Heading",
        background=[("active", "#303055")],
    )

    # ── Scrollbar ─────────────────────────────────────────
    style.configure(
        "Vertical.TScrollbar",
        background=BG_TERTIARY,
        troughcolor=BG_SECONDARY,
        borderwidth=0,
        arrowcolor=TEXT_SECONDARY,
        relief="flat",
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", "#303055")],
        arrowcolor=[("active", TEXT_PRIMARY)],
    )

    # ── Notebook (если останется где-то) ──────────────────
    style.configure(
        "TNotebook",
        background=BG_PRIMARY,
        borderwidth=0,
    )
    style.configure(
        "TNotebook.Tab",
        background=BG_TERTIARY,
        foreground=TEXT_SECONDARY,
        font=FONTS["normal"],
        padding=(16, 8),
        borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", ACCENT), ("active", "#303055")],
        foreground=[("selected", TEXT_PRIMARY), ("active", TEXT_PRIMARY)],
    )

    # ── Separator ─────────────────────────────────────────
    style.configure(
        "TSeparator",
        background=BORDER,
    )
