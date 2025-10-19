import curses
from .component import Component, is_mouse_over
from .terminal_renderer import TerminalRenderer
from .ui_event import UIEvent
from ..utils import _clamp, KEY_ENTER, KEY_BACKSPACE

class Input(Component):
    DEFAULT_FG = curses.COLOR_BLACK
    DEFAULT_BG = curses.COLOR_WHITE
    DEFAULT_FG_FOCUSED = curses.COLOR_WHITE
    DEFAULT_BG_FOCUSED = curses.COLOR_BLUE

    def __init__(self, left, top, width, parent=None, placeholder=""):
        super().__init__(left, top, width, 1, parent)
        self.value = ""
        self.cursor = 0
        self.placeholder = placeholder
        self.fg_color = self.DEFAULT_FG
        self.bg_color = self.DEFAULT_BG
        self.fg_color_focused = self.DEFAULT_FG_FOCUSED
        self.bg_color_focused = self.DEFAULT_BG_FOCUSED

    def set_focused_colors(self, fg=None, bg=None):
        if fg is not None:
            self.fg_color_focused = fg
        if bg is not None:
            self.bg_color_focused = bg

    def render(self, renderer: TerminalRenderer):
        if not self.visibility:
            return
        absolute_x, absolute_y = self.get_absolute_position()
        display = self.value if self.value else self.placeholder
        fg = self.fg_color_focused if self.isFocused else self.fg_color
        bg = self.bg_color_focused if self.isFocused else self.bg_color
        renderer.draw_text(absolute_x, absolute_y, display[:self.width].ljust(self.width), fg, bg)
        if self.isFocused:
            curses.curs_set(1)
            try:
                display_width = sum(1 if ord(c) < 128 else 2 for c in self.value[:self.cursor])
                renderer.screen.move(absolute_y, absolute_x + _clamp(display_width, 0, self.width - 1))
            except curses.error:
                pass
        else:
            curses.curs_set(0)

    def handleEvent(self, event: UIEvent) -> bool:
        if event.type == "key":
            key = event.data.get('key')
            if isinstance(key, str) and key not in ('\n', '\t', '\b'):
                self.value = self.value[:self.cursor] + key + self.value[self.cursor:]
                self.cursor += 1
                return True
            if isinstance(key, int):
                if key in (KEY_BACKSPACE, curses.KEY_BACKSPACE):
                    if self.cursor > 0:
                        self.value = self.value[:self.cursor - 1] + self.value[self.cursor:]
                        self.cursor -= 1
                    return True
                if key == curses.KEY_LEFT:
                    self.cursor = max(0, self.cursor - 1)
                    return True
                if key == curses.KEY_RIGHT:
                    self.cursor = min(len(self.value), self.cursor + 1)
                    return True
                if key == KEY_ENTER:
                    self.dispatchEvent("onsubmit", value=self.value)
                    return True
        if event.type == "mouse":
            mouse_x, mouse_y = event.data['x'], event.data['y']
            if is_mouse_over(self, mouse_x, mouse_y):
                absolute_x, absolute_y = self.get_absolute_position()
                display_widths = [0] + [sum(1 if ord(c) < 128 else 2 for c in self.value[:i+1]) for i in range(len(self.value))]
                mx_rel = mouse_x - (absolute_x + 1)
                self.cursor = next((i for i, w in enumerate(display_widths) if w > mx_rel), len(self.value))
                self.isFocused = True
                return True
        return False