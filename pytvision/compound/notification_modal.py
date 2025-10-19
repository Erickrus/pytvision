import curses
from ..component.component import Component
from ..component.modal import Modal
from ..component.label import Label
from ..component.button import Button

class NotificationModal(Modal):
    DEFAULT_MESSAGE_FG = curses.COLOR_BLACK
    DEFAULT_MESSAGE_BG = 20
    DEFAULT_BUTTON_FG = curses.COLOR_BLACK
    DEFAULT_BUTTON_BG = curses.COLOR_GREEN

    def __init__(self, message: str, parent=None):
        super().__init__(40, 8, "Notification", parent)
        self.message = message
        self.label = Label(2, 2, 36, 3, text=message, parent=self)
        self.label.set_colors(self.DEFAULT_MESSAGE_FG, self.DEFAULT_MESSAGE_BG)
        self.ok_button = Button(14, 5, 8, "OK", parent=self, window=self, onclick=lambda: self.manager.remove(self))
        self.ok_button.set_colors(self.DEFAULT_BUTTON_FG, self.DEFAULT_BUTTON_BG)
        self.add(self.label)
        self.add(self.ok_button)