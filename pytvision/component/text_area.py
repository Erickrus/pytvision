import curses
from .component import Component, is_mouse_over
from .terminal_renderer import TerminalRenderer
from .ui_event import UIEvent
from ..utils import _clamp, _safe_add_string, KEY_ENTER, KEY_BACKSPACE

class TextArea(Component):
    DEFAULT_FG = curses.COLOR_BLACK
    DEFAULT_BG = curses.COLOR_WHITE
    DEFAULT_FG_FOCUSED = curses.COLOR_WHITE
    DEFAULT_BG_FOCUSED = curses.COLOR_BLUE
    DEFAULT_BORDER_FG = curses.COLOR_BLACK
    DEFAULT_BORDER_BG = curses.COLOR_WHITE
    DEFAULT_SCROLLBAR_FG = curses.COLOR_WHITE
    DEFAULT_SCROLLBAR_BG = 20
    DEFAULT_HILITE_FG = curses.COLOR_BLACK
    DEFAULT_HILITE_BG = curses.COLOR_RED

    def __init__(self, left, top, width, height, parent=None, value=""):
        super().__init__(left, top, width, height, parent)
        self.lines = value.splitlines() or [""]
        self.cx = 0
        self.cy = 0
        self.view_top = 0
        self.fg_color = self.DEFAULT_FG
        self.bg_color = self.DEFAULT_BG
        self.fg_color_focused = self.DEFAULT_FG_FOCUSED
        self.bg_color_focused = self.DEFAULT_BG_FOCUSED
        self.border_fg = self.DEFAULT_BORDER_FG
        self.border_bg = self.DEFAULT_BORDER_BG
        self.scrollbar_fg = self.DEFAULT_SCROLLBAR_FG
        self.scrollbar_bg = self.DEFAULT_SCROLLBAR_BG
        self.hilite_fg = self.DEFAULT_HILITE_FG
        self.hilite_bg = self.DEFAULT_HILITE_BG

    def set_focused_colors(self, fg=None, bg=None):
        if fg is not None:
            self.fg_color_focused = fg
        if bg is not None:
            self.bg_color_focused = bg

    def set_border_colors(self, fg=None, bg=None):
        if fg is not None:
            self.border_fg = fg
        if bg is not None:
            self.border_bg = bg

    def set_scrollbar_colors(self, fg=None, bg=None):
        if fg is not None:
            self.scrollbar_fg = fg
        if bg is not None:
            self.scrollbar_bg = bg

    def set_hilite_colors(self, fg=None, bg=None):
        if fg is not None:
            self.hilite_fg = fg
        if bg is not None:
            self.hilite_bg = bg

    def set_value(self, value):
        self.lines = value.splitlines() or [""]
        self.cx = self.cy = self.view_top = 0

    def get_value(self):
        return "\n".join(self.lines)

    def render(self, renderer: TerminalRenderer):
        if not self.visibility:
            return
        absolute_x, absolute_y = self.get_absolute_position()
        renderer.draw_box(absolute_x, absolute_y, self.width, self.height, title=None, win=renderer.screen, fg=self.border_fg, bg=self.border_bg, border_style="single")
        inner_h = self.height - 2
        inner_w = self.width - 2
        has_scrollbar = len(self.lines) > inner_h
        text_w = inner_w - 1 if has_scrollbar else inner_w
        for i in range(inner_h):
            idx = self.view_top + i
            if idx < len(self.lines):
                s = self.lines[idx]
                fg = self.fg_color_focused if self.isFocused else self.fg_color
                bg = self.bg_color_focused if self.isFocused else self.bg_color
                if self.isFocused and idx == self.cy and self.cx < len(s):
                    before_cursor = s[:self.cx]
                    cursor_char = s[self.cx:self.cx+1] or " "
                    after_cursor = s[self.cx + 1:][:text_w - self.cx - 1]
                    renderer.draw_text(absolute_x + 1, absolute_y + 1 + i, before_cursor, fg, bg)
                    renderer.draw_text(absolute_x + 1 + len(before_cursor), absolute_y + 1 + i, cursor_char, self.hilite_fg, self.hilite_bg)
                    renderer.draw_text(absolute_x + 1 + len(before_cursor) + len(cursor_char), absolute_y + 1 + i, after_cursor.ljust(text_w - len(before_cursor) - len(cursor_char)), fg, bg)
                else:
                    renderer.draw_text(absolute_x + 1, absolute_y + 1 + i, s[:text_w].ljust(text_w), fg, bg)
            else:
                renderer.draw_text(absolute_x + 1, absolute_y + 1 + i, " " * text_w, fg, bg)
        if has_scrollbar:
            sbar_x = absolute_x + self.width - 2
            scrollbar_attr = renderer.get_color_pair(self.scrollbar_fg, self.scrollbar_bg)
            for i in range(inner_h):
                _safe_add_string(renderer.screen, absolute_y + 1 + i, sbar_x, '│', scrollbar_attr)
            thumb_size = max(1, inner_h * inner_h // len(self.lines))
            thumb_pos = inner_h * self.view_top // len(self.lines)
            for i in range(thumb_size):
                _safe_add_string(renderer.screen, absolute_y + 1 + thumb_pos + i, sbar_x, '█',
                               renderer.get_color_pair(self.hilite_fg, self.hilite_bg))
        curses.curs_set(0)

    def handleEvent(self, event: UIEvent) -> bool:
        if event.type == "key":
            key = event.data.get('key')
            if isinstance(key, str) and key not in ('\n', '\t', '\b'):
                line = self.lines[self.cy]
                self.lines[self.cy] = line[:self.cx] + key + line[self.cx:]
                self.cx += 1
                return True
            if isinstance(key, int):
                if key in (KEY_BACKSPACE, curses.KEY_BACKSPACE):
                    if self.cx > 0:
                        line = self.lines[self.cy]
                        self.lines[self.cy] = line[:self.cx - 1] + line[self.cx:]
                        self.cx -= 1
                    elif self.cy > 0:
                        prev = self.lines[self.cy - 1]
                        cur = self.lines.pop(self.cy)
                        self.cy -= 1
                        self.cx = len(prev)
                        self.lines[self.cy] = prev + cur
                    return True
                if key in (KEY_ENTER, curses.KEY_ENTER):
                    line = self.lines[self.cy]
                    left = line[:self.cx]
                    right = line[self.cx:]
                    self.lines[self.cy] = left
                    self.cy += 1
                    self.cx = 0
                    self.lines.insert(self.cy, right)
                    if self.cy >= self.view_top + (self.height - 2):
                        self.view_top = self.cy - (self.height - 3)
                    return True
                if key == curses.KEY_UP:
                    if self.cy > 0:
                        self.cy -= 1
                        self.cx = min(self.cx, len(self.lines[self.cy]))
                        if self.cy < self.view_top:
                            self.view_top = self.cy
                    return True
                if key == curses.KEY_DOWN:
                    if self.cy < len(self.lines) - 1:
                        self.cy += 1
                        self.cx = min(self.cx, len(self.lines[self.cy]))
                        if self.cy >= self.view_top + (self.height - 2):
                            self.view_top += 1
                    return True
                if key == curses.KEY_LEFT:
                    if self.cx > 0:
                        self.cx -= 1
                    elif self.cy > 0:
                        self.cy -= 1
                        self.cx = len(self.lines[self.cy])
                    return True
                if key == curses.KEY_RIGHT:
                    if self.cx < len(self.lines[self.cy]):
                        self.cx += 1
                    elif self.cy < len(self.lines) - 1:
                        self.cy += 1
                        self.cx = 0
                    return True
                if key in (curses.KEY_PPAGE,):
                    self.view_top = max(0, self.view_top - (self.height - 2))
                    return True
                if key in (curses.KEY_NPAGE,):
                    self.view_top = min(max(0, len(self.lines) - (self.height - 2)), self.view_top + (self.height - 2))
                    return True
        if event.type == "mouse":
            mouse_x, mouse_y = event.data['x'], event.data['y']
            if is_mouse_over(self, mouse_x, mouse_y):
                absolute_x, absolute_y = self.get_absolute_position()
                row = mouse_y - (absolute_y + 1)
                self.cy = _clamp(self.view_top + row, 0, len(self.lines) - 1)
                col = mouse_x - (absolute_x + 1)
                self.cx = _clamp(col, 0, len(self.lines[self.cy]))
                self.isFocused = True
                return True
        return False