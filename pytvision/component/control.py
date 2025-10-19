import curses
from .component import Component
from .terminal_renderer import TerminalRenderer
from .ui_event import UIEvent

class Label(Component):
    DEFAULT_FG = curses.COLOR_BLACK
    DEFAULT_BG = 20  # Light gray

    def __init__(self, left, top, width, height, text: str = "", parent=None):
        super().__init__(left, top, width, height, parent)
        self.text = text
        self.fg_color = self.DEFAULT_FG
        self.bg_color = self.DEFAULT_BG

    def render(self, renderer: TerminalRenderer):
        if not self.visibility:
            return
        absolute_x, absolute_y = self.get_absolute_position()
        lines = self.text.splitlines()
        for i, ln in enumerate(lines[:self.height]):
            renderer.draw_text(absolute_x, absolute_y + i, ln[:self.width], self.fg_color, self.bg_color)

    def handleEvent(self, event: UIEvent) -> bool:
        return False