import curses
from .input import Input
from .terminal_renderer import TerminalRenderer
from ..utils import _clamp

class Password(Input):
    def __init__(self, left, top, width, parent=None, mask='*'):
        super().__init__(left, top, width, parent)
        self.mask = mask
        self.show = False

    def render(self, renderer: TerminalRenderer):
        if not self.visibility:
            return
        absolute_x, absolute_y = self.get_absolute_position()
        display = self.value if self.show else (self.mask * len(self.value))
        fg = self.fg_color_focused if self.isFocused else self.fg_color
        bg = self.bg_color_focused if self.isFocused else self.bg_color
        renderer.draw_text(absolute_x, absolute_y, display[:self.width].ljust(self.width), fg, bg)
        if self.isFocused:
            curses.curs_set(1)
            try:
                renderer.screen.move(absolute_y, absolute_x + _clamp(self.cursor, 0, self.width - 1))
            except curses.error:
                pass
        else:
            curses.curs_set(0)