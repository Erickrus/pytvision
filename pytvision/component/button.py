import curses
from typing import Optional, Callable

from ..utils import _safe_add_string, KEY_ENTER
from .component import Component, is_mouse_over
from .terminal_renderer import TerminalRenderer
from .ui_event import UIEvent


class Button(Component):
    DEFAULT_FG = curses.COLOR_BLACK
    DEFAULT_BG = curses.COLOR_GREEN
    DEFAULT_FG_FOCUSED = curses.COLOR_BLACK
    DEFAULT_BG_FOCUSED = curses.COLOR_YELLOW
    DEFAULT_SHADOW_FG = curses.COLOR_BLACK
    DEFAULT_SHADOW_BG = curses.COLOR_BLACK

    def __init__(self, left, top, width, label: str, parent=None, window=None, onclick: Optional[Callable] = None):
        super().__init__(left, top, width, 1, parent)
        self.label = label
        self.window = window
        self.onclick = onclick
        self.fg_color = self.DEFAULT_FG
        self.bg_color = self.DEFAULT_BG
        self.fg_color_focused = self.DEFAULT_FG_FOCUSED
        self.bg_color_focused = self.DEFAULT_BG_FOCUSED
        self.shadow_fg = self.DEFAULT_SHADOW_FG
        self.shadow_bg = self.DEFAULT_SHADOW_BG

    def set_focused_colors(self, fg=None, bg=None):
        if fg is not None:
            self.fg_color_focused = fg
        if bg is not None:
            self.bg_color_focused = bg

    def set_shadow_colors(self, fg=None, bg=None):
        if fg is not None:
            self.shadow_fg = fg
        if bg is not None:
            self.shadow_bg = bg

    def render(self, renderer: TerminalRenderer):
        if not self.visibility:
            return
        absolute_x, absolute_y = self.get_absolute_position()
        fg = self.fg_color_focused if self.isFocused else self.fg_color
        bg = self.bg_color_focused if self.isFocused else self.bg_color
        txt = self.label.center(self.width)
        _safe_add_string(renderer.screen, absolute_y, absolute_x, txt, renderer.get_color_pair(fg, bg))
        if self.width > 0 and self.height > 0:
            _safe_add_string(renderer.screen, absolute_y + 1, absolute_x + 1, "▀" * self.width, renderer.get_color_pair(self.shadow_fg, self.shadow_bg))
            _safe_add_string(renderer.screen, absolute_y, absolute_x + self.width, "▀", renderer.get_color_pair(self.shadow_fg, self.shadow_bg))

    def handleEvent(self, event: UIEvent) -> bool:
        if event.type == "key" and event.data.get('key') in (KEY_ENTER, 32):
            if self.onclick:
                self.onclick()
            return True
        if event.type == "mouse":
            mouse_x, mouse_y = event.data['x'], event.data['y']
            bstate = event.data.get('bstate', 0)
            if is_mouse_over(self, mouse_x, mouse_y):
                if bstate & (curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED):
                    self.isFocused = True
                    if bstate & curses.BUTTON1_PRESSED and self.onclick:
                        self.onclick()
                    return True
        return False