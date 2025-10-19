import curses
from ..utils import _safe_add_string
from typing import Optional

class TerminalRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.h, self.w = screen.getmaxyx()
        self.init_colors()

    def init_colors(self):
        curses.start_color()
        curses.use_default_colors()
        self.color_pairs = {}
        self.next_pair = 1
        self.light_gray_bg = curses.COLOR_WHITE
        self.true_white_fg = curses.COLOR_WHITE
        if curses.can_change_color():
            try:
                curses.init_color(21, 1000, 1000, 1000)  # True white
                self.true_white_fg = 21
                curses.init_color(20, 700, 700, 700)  # Light gray
                self.light_gray_bg = 20
            except Exception:
                self.true_white_fg = curses.COLOR_WHITE

    def get_color_pair(self, fg, bg):
        key = (fg, bg)
        if key not in self.color_pairs:
            curses.init_pair(self.next_pair, fg, bg)
            self.color_pairs[key] = self.next_pair
            self.next_pair += 1
        return curses.color_pair(self.color_pairs[key])

    def refresh_dimensions(self):
        self.h, self.w = self.screen.getmaxyx()

    def draw_box(self, x: int, y: int, w: int, h: int, title: Optional[str] = None, win=None, fg=curses.COLOR_WHITE, bg=curses.COLOR_BLUE, fill=False, border_style="double"):
        if w <= 0 or h <= 0:
            return
        if win is None:
            win = self.screen
        attr = self.get_color_pair(fg, bg)
        tl, tr, bl, br, hor, ver = ('┌', '┐', '└', '┘', '─', '│') if border_style == "single" else ('╔', '╗', '╚', '╝', '═', '║')
        _safe_add_string(win, y, x, tl + hor * (w - 2) + tr, attr)
        for i in range(1, h - 1):
            _safe_add_string(win, y + i, x, ver, attr)
            _safe_add_string(win, y + i, x + 1, (" " * (w - 2) if not fill else " " * (w - 2)), attr)
            _safe_add_string(win, y + i, x + w - 1, ver, attr)
        _safe_add_string(win, y + h - 1, x, bl + hor * (w - 2) + br, attr)
        if title:
            t = f" {title} "
            if len(t) < w - 2:
                _safe_add_string(win, y, x + 2, t, attr | curses.A_BOLD)

    def draw_shadow(self, x: int, y: int, w: int, h: int, win=None):
        if win is None:
            win = self.screen
        sattr = self.get_color_pair(curses.COLOR_BLACK, curses.COLOR_BLACK)
        for i in range(h):
            if 0 <= y + i < self.h and 0 <= x + w < self.w:
                _safe_add_string(win, y + i, x + w, " ", sattr)
        if 0 <= y + h < self.h:
            _safe_add_string(win, y + h, x + 1, " " * w, sattr)

    def draw_text(self, x, y, text, fg=curses.COLOR_WHITE, bg=-1):
        if y < 0 or y >= self.h:
            return
        if x < 0:
            text = text[-x:]
            x = 0
        if x >= self.w:
            return
        text = text[:max(0, self.w - x)]
        _safe_add_string(self.screen, y, x, text, self.get_color_pair(fg, bg))
