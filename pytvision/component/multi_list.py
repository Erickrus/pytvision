import curses

from typing import List, Dict


from .component import Component, is_mouse_over
from .terminal_renderer import TerminalRenderer
from .ui_event import UIEvent
from ..utils import KEY_ENTER

class MultiList(Component):
    DEFAULT_FG = -1
    DEFAULT_BG = curses.COLOR_WHITE
    DEFAULT_BORDER_FG = curses.COLOR_BLACK
    DEFAULT_BORDER_BG = curses.COLOR_WHITE
    DEFAULT_HILITE_FG = curses.COLOR_BLACK
    DEFAULT_HILITE_BG = curses.COLOR_CYAN

    def __init__(self, left, top, width, height, items: List[str], parent=None):
        super().__init__(left, top, width, height, parent)
        self.items = items[:]
        self.selectedItems: Dict[int, bool] = {}
        self.view_top = 0
        self.cursor = 0
        self.fg_color = self.DEFAULT_FG
        self.bg_color = self.DEFAULT_BG
        self.border_fg = self.DEFAULT_BORDER_FG
        self.border_bg = self.DEFAULT_BORDER_BG
        self.hilite_fg = self.DEFAULT_HILITE_FG
        self.hilite_bg = self.DEFAULT_HILITE_BG

    def set_border_colors(self, fg=None, bg=None):
        if fg is not None:
            self.border_fg = fg
        if bg is not None:
            self.border_bg = bg

    def set_hilite_colors(self, fg=None, bg=None):
        if fg is not None:
            self.hilite_fg = fg
        if bg is not None:
            self.hilite_bg = bg

    def render(self, renderer: TerminalRenderer):
        if not self.visibility:
            return
        absolute_x, absolute_y = self.get_absolute_position()
        renderer.draw_box(absolute_x, absolute_y, self.width, self.height, title=None, win=renderer.screen, fg=self.border_fg, bg=self.border_bg, border_style="single")
        inner_h = self.height - 2
        for i in range(inner_h):
            idx = self.view_top + i
            if idx < len(self.items):
                item = self.items[idx]
                selection = "[X]" if self.selectedItems.get(idx, False) else "[ ]"
                txt = f"{selection} {item}"[:self.width - 2].ljust(self.width - 2)
                fg = self.hilite_fg if self.isFocused and idx == self.cursor else self.fg_color
                bg = self.hilite_bg if self.isFocused and idx == self.cursor else self.bg_color
                renderer.draw_text(absolute_x + 1, absolute_y + 1 + i, txt, fg, bg)
            else:
                renderer.draw_text(absolute_x + 1, absolute_y + 1 + i, " " * (self.width - 2), self.fg_color, self.bg_color)

    def handleEvent(self, event: UIEvent) -> bool:
        if event.type == "key":
            key = event.data.get('key')
            if key == curses.KEY_UP:
                self.cursor = max(0, self.cursor - 1)
                if self.cursor < self.view_top:
                    self.view_top = self.cursor
                return True
            if key == curses.KEY_DOWN:
                self.cursor = min(len(self.items) - 1, self.cursor + 1)
                if self.cursor >= self.view_top + (self.height - 2):
                    self.view_top = self.cursor - (self.height - 3)
                return True
            if key in (KEY_ENTER, 32):
                self.selectedItems[self.cursor] = not self.selectedItems.get(self.cursor, False)
                return True
            if key == curses.KEY_PPAGE:
                self.view_top = max(0, self.view_top - (self.height - 2))
                return True
            if key == curses.KEY_NPAGE:
                self.view_top = min(max(0, len(self.items) - (self.height - 2)), self.view_top + (self.height - 2))
                return True
        if event.type == "mouse":
            mouse_x, mouse_y = event.data['x'], event.data['y']
            bstate = event.data.get('bstate', 0)
            if is_mouse_over(self, mouse_x, mouse_y):
                self.isFocused = True
                absolute_x, absolute_y = self.get_absolute_position()
                row = mouse_y - (absolute_y + 1)
                idx = self.view_top + row
                if 0 <= idx < len(self.items):
                    self.cursor = idx
                    if bstate & curses.BUTTON1_CLICKED:
                        self.selectedItems[idx] = not self.selectedItems.get(idx, False)
                    return True
        return False