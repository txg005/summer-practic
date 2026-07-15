import tkinter as tk

class Tooltip:
    def __init__(self, widget, text: str, delay: int = 600):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._id = None
        self._tip = None
        widget.bind('<Enter>', self._schedule)
        widget.bind('<Leave>', self._cancel)

    def _schedule(self, event=None):
        self._cancel()
        self._id = self.widget.after(self.delay, self._show)

    def _cancel(self, event=None):
        if self._id:
            self.widget.after_cancel(self._id)
            self._id = None
        if self._tip:
            self._tip.destroy()
            self._tip = None

    def _show(self):
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f'+{x}+{y}')
        tk.Label(self._tip, text=self.text, justify='left',
                 background='#ffffcc', relief='solid', borderwidth=1,
                 font=('TkDefaultFont', 9), padx=6, pady=4).pack()