import curses
from .component import Component, is_mouse_over
from .ui_event import UIEvent
from .terminal_renderer import TerminalRenderer
from ..utils import KEY_ENTER

class CheckBox(Component):
    DEFAULT_FG = curses.COLOR_WHITE
    DEFAULT_BG = -1

    def __init__(self, left, top, label, parent=None, isChecked=False):
        super().__init__(left, top, len(label) + 4, 1, parent)
        self.label = label
        self.isChecked = isChecked
        self.fg_color = self.DEFAULT_FG
        self.bg_color = self.DEFAULT_BG

    def render(self, renderer: TerminalRenderer):
        if not self.visibility:
            return
        absolute_x, absolute_y = self.get_absolute_position()
        ch = "[x]" if self.isChecked else "[ ]"
        renderer.draw_text(absolute_x, absolute_y, f"{ch} {self.label}", self.fg_color, self.bg_color)

    def handleEvent(self, event: UIEvent) -> bool:
        if event.type == "mouse":
            mouse_x, mouse_y = event.data['x'], event.data['y']
            if is_mouse_over(self, mouse_x, mouse_y):
                if event.data.get('bstate', 0) & curses.BUTTON1_CLICKED:
                    self.isChecked = not self.isChecked
                    return True
        if event.type == "key" and event.data.get('key') in (KEY_ENTER, 32):
            self.isChecked = not self.isChecked
            return True
        return False