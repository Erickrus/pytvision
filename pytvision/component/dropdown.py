import curses

from typing import List

from .component import Component, is_mouse_over
from .terminal_renderer import TerminalRenderer
from .ui_event import UIEvent
from ..utils import _safe_add_string, _clamp, KEY_ENTER, KEY_ESC

class Dropdown(Component):
    DEFAULT_FG = curses.COLOR_BLACK
    DEFAULT_BG = curses.COLOR_WHITE
    DEFAULT_FG_FOCUSED = curses.COLOR_WHITE
    DEFAULT_BG_FOCUSED = curses.COLOR_BLUE
    DEFAULT_BUTTON_FG = curses.COLOR_BLACK
    DEFAULT_BUTTON_BG = curses.COLOR_GREEN
    DEFAULT_DROPDOWN_FG = curses.COLOR_WHITE
    DEFAULT_DROPDOWN_BG = curses.COLOR_BLUE
    DEFAULT_DROPDOWN_HILITE_FG = curses.COLOR_WHITE
    DEFAULT_DROPDOWN_HILITE_BG = curses.COLOR_CYAN
    DEFAULT_BORDER_FG = curses.COLOR_BLACK
    DEFAULT_BORDER_BG = 20

    def __init__(self, left, top, width, items: List[str], parent=None):
        super().__init__(left, top, width, 1, parent)
        self.items = items[:]
        self.selectedIndex = None
        self.cursor = 0
        self.dropdown_open = False
        self.view_top = 0
        self.fg_color = self.DEFAULT_FG
        self.bg_color = self.DEFAULT_BG
        self.fg_color_focused = self.DEFAULT_FG_FOCUSED
        self.bg_color_focused = self.DEFAULT_BG_FOCUSED
        self.button_fg = self.DEFAULT_BUTTON_FG
        self.button_bg = self.DEFAULT_BUTTON_BG
        self.dropdown_fg = self.DEFAULT_DROPDOWN_FG
        self.dropdown_bg = self.DEFAULT_DROPDOWN_BG
        self.dropdown_hilite_fg = self.DEFAULT_DROPDOWN_HILITE_FG
        self.dropdown_hilite_bg = self.DEFAULT_DROPDOWN_HILITE_BG
        self.border_fg = self.DEFAULT_BORDER_FG
        self.border_bg = self.DEFAULT_BORDER_BG
        self.dropdown_height = min(len(self.items), 6) + 2
        self.dragging_scrollbar = False
        self.drag_start_y = 0

    def set_focused_colors(self, fg=None, bg=None):
        if fg is not None:
            self.fg_color_focused = fg
        if bg is not None:
            self.bg_color_focused = bg

    def set_button_colors(self, fg=None, bg=None):
        if fg is not None:
            self.button_fg = fg
        if bg is not None:
            self.button_bg = bg

    def set_dropdown_colors(self, fg=None, bg=None, hilite_fg=None, hilite_bg=None):
        if fg is not None:
            self.dropdown_fg = fg
        if bg is not None:
            self.dropdown_bg = bg
        if hilite_fg is not None:
            self.dropdown_hilite_fg = hilite_fg
        if hilite_bg is not None:
            self.dropdown_hilite_bg = hilite_bg

    def set_border_colors(self, fg=None, bg=None):
        if fg is not None:
            self.border_fg = fg
        if bg is not None:
            self.border_bg = bg

    def get_value(self):
        return self.items[self.selectedIndex] if self.selectedIndex is not None else ""

    def render(self, renderer: TerminalRenderer):
        if not self.visibility:
            return
        absolute_x, absolute_y = self.get_absolute_position()
        fg = self.fg_color_focused if self.isFocused else self.fg_color
        bg = self.bg_color_focused if self.isFocused else self.bg_color
        display_text = self.get_value()[:self.width - 3].ljust(self.width - 3)
        renderer.draw_text(absolute_x, absolute_y, display_text, fg, bg)
        _safe_add_string(renderer.screen, absolute_y, absolute_x + self.width - 2, "⬇ ", renderer.get_color_pair(self.button_fg, self.button_bg))
        if self.dropdown_open:
            renderer.draw_box(absolute_x, absolute_y + 1, self.width, self.dropdown_height, title=None, win=renderer.screen,
                            fg=self.border_fg, bg=self.border_bg, border_style="single")
            inner_h = self.dropdown_height - 2
            for i in range(inner_h):
                idx = self.view_top + i
                if idx < len(self.items):
                    txt = self.items[idx][:self.width - 3].ljust(self.width - 3)
                    fg = self.dropdown_hilite_fg if idx == self.cursor else self.dropdown_fg
                    bg = self.dropdown_hilite_bg if idx == self.cursor else self.dropdown_bg
                    renderer.draw_text(absolute_x + 1, absolute_y + 2 + i, txt, fg, bg)
                else:
                    renderer.draw_text(absolute_x + 1, absolute_y + 2 + i, " " * (self.width - 3), self.dropdown_fg, self.dropdown_bg)
            if len(self.items) > inner_h:
                sbar_x = absolute_x + self.width - 2
                scrollbar_attr = renderer.get_color_pair(self.dropdown_fg, self.dropdown_bg)
                for i in range(inner_h):
                    _safe_add_string(renderer.screen, absolute_y + 2 + i, sbar_x, '│', scrollbar_attr)
                thumb_size = max(1, inner_h * inner_h // len(self.items))
                thumb_pos = inner_h * self.view_top // len(self.items)
                for i in range(thumb_size):
                    _safe_add_string(renderer.screen, absolute_y + 2 + thumb_pos + i, sbar_x, '█',
                                   renderer.get_color_pair(self.dropdown_hilite_fg, self.dropdown_hilite_bg))
        curses.curs_set(0)

    def handleEvent(self, event: UIEvent) -> bool:
        absolute_x, absolute_y = self.get_absolute_position()
        if event.type == "key":
            key = event.data.get('key')
            if not self.dropdown_open:
                if key in (KEY_ENTER, curses.KEY_DOWN, 32):
                    self.dropdown_open = True
                    self.isFocused = True
                    if self.items:
                        self.cursor = _clamp(self.cursor, 0, len(self.items) - 1)
                    return True
                if key == KEY_ESC:
                    self.isFocused = False
                    self.dropdown_open = False
                    return True
            else:
                if key == curses.KEY_UP:
                    if self.items:
                        self.cursor = max(0, self.cursor - 1)
                        if self.cursor < self.view_top:
                            self.view_top = self.cursor
                    return True
                if key == curses.KEY_DOWN:
                    if self.items:
                        self.cursor = min(len(self.items) - 1, self.cursor + 1)
                        if self.cursor >= self.view_top + (self.dropdown_height - 2):
                            self.view_top = self.cursor - (self.dropdown_height - 3)
                    return True
                if key in (KEY_ENTER, 32):
                    if self.items:
                        self.selectedIndex = self.cursor
                        self.dropdown_open = False
                        self.isFocused = True
                        self.dispatchEvent("onselect", value=self.get_value())
                    return True
                if key == KEY_ESC:
                    self.dropdown_open = False
                    self.isFocused = True
                    return True
                if key == curses.KEY_PPAGE:
                    if self.items:
                        self.view_top = max(0, self.view_top - (self.dropdown_height - 2))
                        self.cursor = max(self.cursor - (self.dropdown_height - 2), 0)
                    return True
                if key == curses.KEY_NPAGE:
                    if self.items:
                        self.view_top = min(max(0, len(self.items) - (self.dropdown_height - 2)),
                                          self.view_top + (self.dropdown_height - 2))
                        self.cursor = min(self.cursor + (self.dropdown_height - 2), len(self.items) - 1)
                    return True
        if event.type == "mouse":
            mouse_x, mouse_y = event.data['x'], event.data['y']
            bstate = event.data.get('bstate', 0)
            inner_h = self.dropdown_height - 2
            dropdown_bounds = (self.dropdown_open and
                             mouse_x >= absolute_x and mouse_x < absolute_x + self.width and
                             mouse_y >= absolute_y and mouse_y < absolute_y + self.dropdown_height)
            input_bounds = is_mouse_over(self, mouse_x, mouse_y)
            if not self.dropdown_open:
                if input_bounds and bstate & (curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED):
                    self.dropdown_open = True
                    self.isFocused = True
                    if self.items:
                        self.cursor = _clamp(self.cursor, 0, len(self.items) - 1)
                    return True
            else:
                if dropdown_bounds and hasattr(curses, 'BUTTON4_PRESSED') and bstate & curses.BUTTON4_PRESSED:
                    if self.items:
                        self.cursor = max(0, self.cursor - 1)
                        if self.cursor < self.view_top:
                            self.view_top = self.cursor
                        self.isFocused = True
                        return True
                if dropdown_bounds and hasattr(curses, 'BUTTON5_PRESSED') and bstate & curses.BUTTON5_PRESSED:
                    if self.items:
                        self.cursor = min(len(self.items) - 1, self.cursor + 1)
                        if self.cursor >= self.view_top + inner_h:
                            self.view_top = self.cursor - (inner_h - 1)
                        self.isFocused = True
                        return True
                if len(self.items) > inner_h and mouse_x == absolute_x + self.width - 2 and absolute_y + 2 <= mouse_y < absolute_y + 2 + inner_h:
                    if bstate & curses.BUTTON1_PRESSED:
                        self.dragging_scrollbar = True
                        self.drag_start_y = mouse_y
                        thumb_size = max(1, inner_h * inner_h // len(self.items))
                        thumb_pos = inner_h * self.view_top // len(self.items)
                        if mouse_y < absolute_y + 2 + thumb_pos or mouse_y >= absolute_y + 2 + thumb_pos + thumb_size:
                            if mouse_y < absolute_y + 2 + thumb_pos:
                                self.view_top = max(0, self.view_top - inner_h)
                            else:
                                self.view_top = min(len(self.items) - inner_h, self.view_top + inner_h)
                            self.cursor = _clamp(self.cursor, self.view_top, self.view_top + inner_h - 1)
                        self.isFocused = True
                        return True
                    elif bstate & curses.BUTTON1_RELEASED:
                        self.dragging_scrollbar = False
                        self.isFocused = True
                        return True
                elif self.dragging_scrollbar and bstate & curses.REPORT_MOUSE_POSITION:
                    delta_y = mouse_y - self.drag_start_y
                    max_view_top = max(0, len(self.items) - inner_h)
                    scroll_range = inner_h - (inner_h * inner_h // len(self.items))
                    if scroll_range > 0:
                        view_top_delta = (delta_y * max_view_top) // scroll_range
                        self.view_top = _clamp(self.view_top + view_top_delta, 0, max_view_top)
                        self.drag_start_y = mouse_y
                        self.cursor = _clamp(self.cursor, self.view_top, min(len(self.items) - 1, self.view_top + inner_h - 1))
                    self.isFocused = True
                    return True
                elif bstate & curses.BUTTON1_RELEASED:
                    self.dragging_scrollbar = False
                    self.isFocused = True
                    return True
                if self.dropdown_open and mouse_y >= absolute_y + 2 and mouse_y < absolute_y + 2 + inner_h and mouse_x >= absolute_x + 1 and mouse_x < absolute_x + self.width - 1:
                    idx = self.view_top + (mouse_y - (absolute_y + 2))
                    if 0 <= idx < len(self.items):
                        self.cursor = idx
                        if bstate & (curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED):
                            self.selectedIndex = self.cursor
                            self.dropdown_open = False
                            self.isFocused = True
                            self.dispatchEvent("onselect", value=self.get_value())
                        return True
                if input_bounds and bstate & (curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED):
                    self.isFocused = True
                    return True
                if not dropdown_bounds and bstate & (curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED):
                    self.dropdown_open = False
                    self.isFocused = False
                    return True
                if dropdown_bounds:
                    self.isFocused = True
                    return True
        return False
