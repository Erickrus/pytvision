import curses
from ..component.component import Component
from ..component.modal import Modal
from ..component.label import Label
from ..component.button import Button

from typing import Optional, Callable

class ConfirmModal(Modal):
    DEFAULT_MESSAGE_FG = curses.COLOR_BLACK
    DEFAULT_MESSAGE_BG = 20
    DEFAULT_BUTTON_FG = curses.COLOR_BLACK
    DEFAULT_BUTTON_BG = curses.COLOR_GREEN

    def __init__(self, message: str, parent=None, on_confirm: Optional[Callable] = None):
        super().__init__(40, 10, "Confirm", parent)
        self.message = message
        self.on_confirm = on_confirm
        self.label = Label(2, 2, 36, 4, text=message, parent=self)
        self.label.set_colors(self.DEFAULT_MESSAGE_FG, self.DEFAULT_MESSAGE_BG)
        self.ok_button = Button(8, 6, 8, "OK", parent=self, window=self, onclick=self.on_ok)
        self.ok_button.set_colors(self.DEFAULT_BUTTON_FG, self.DEFAULT_BUTTON_BG)
        self.cancel_button = Button(24, 6, 10, "Cancel", parent=self, window=self, onclick=lambda: self.manager.remove(self))
        self.cancel_button.set_colors(self.DEFAULT_BUTTON_FG, self.DEFAULT_BUTTON_BG)
        self.add(self.label)
        self.add(self.ok_button)
        self.add(self.cancel_button)

    def on_ok(self):
        if self.on_confirm:
            self.on_confirm()
        self.manager.remove(self)
