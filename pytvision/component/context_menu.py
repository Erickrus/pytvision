import curses
from typing import List

from .component import Component
from .terminal_renderer import TerminalRenderer
from .ui_event import UIEvent
from .menu_item import MenuItem

from ..utils import _split_mnemonic, _safe_add_string, KEY_ENTER, KEY_ESC


class ContextMenu(Component):
    DEFAULT_FG = curses.COLOR_BLACK
    DEFAULT_BG = 20
    DEFAULT_SELECTED_FG = curses.COLOR_BLACK
    DEFAULT_SELECTED_BG = curses.COLOR_GREEN
    DEFAULT_HOTKEY_FG = curses.COLOR_RED
    DEFAULT_HOTKEY_BG = 20
    DEFAULT_HOTKEY_SELECTED_FG = curses.COLOR_RED
    DEFAULT_HOTKEY_SELECTED_BG = curses.COLOR_GREEN
    DEFAULT_BORDER_FG = curses.COLOR_BLACK
    DEFAULT_BORDER_BG = 20

    def __init__(self, left, top, width=24, parent=None):
        super().__init__(left, top, width, 6, parent)
        self.items: List[MenuItem] = []
        self.selectedIndex = 0
        self.opened = False
        self.fg_color = self.DEFAULT_FG
        self.bg_color = self.DEFAULT_BG
        self.selected_fg = self.DEFAULT_SELECTED_FG
        self.selected_bg = self.DEFAULT_SELECTED_BG
        self.hotkey_fg = self.DEFAULT_HOTKEY_FG
        self.hotkey_bg = self.DEFAULT_HOTKEY_BG
        self.hotkey_selected_fg = self.DEFAULT_HOTKEY_SELECTED_FG
        self.hotkey_selected_bg = self.DEFAULT_HOTKEY_SELECTED_BG
        self.border_fg = self.DEFAULT_BORDER_FG
        self.border_bg = self.DEFAULT_BORDER_BG

    def set_selected_colors(self, fg=None, bg=None):
        if fg is not None:
            self.selected_fg = fg
        if bg is not None:
            self.selected_bg = bg

    def set_hotkey_colors(self, fg=None, bg=None, selected_fg=None, selected_bg=None):
        if fg is not None:
            self.hotkey_fg = fg
        if bg is not None:
            self.hotkey_bg = bg
        if selected_fg is not None:
            self.hotkey_selected_fg = selected_fg
        if selected_bg is not None:
            self.hotkey_selected_bg = selected_bg

    def set_border_colors(self, fg=None, bg=None):
        if fg is not None:
            self.border_fg = fg
        if bg is not None:
            self.border_bg = bg

    def add(self, item: MenuItem):
        self.items.append(item)
        self.height = max(3, min(2 + len(self.items), 20))

    def render(self, renderer: TerminalRenderer):
        if not self.visibility or not self.opened:
            return
        absolute_x, absolute_y = self.get_absolute_position()
        renderer.draw_box(absolute_x, absolute_y, self.width, self.height, title=None, win=renderer.screen, fg=self.border_fg, bg=self.border_bg, border_style="double")
        inner_w = self.width - 2
        for i, item in enumerate(self.items[:self.height - 2]):
            label, mn, pos = _split_mnemonic(item.label)
            txt = label
            if item.shortcut:
                pad = inner_w - len(label) - len(item.shortcut) - 1
                txt = label + " " * max(0, pad) + item.shortcut
            fg = self.selected_fg if i == self.selectedIndex else self.fg_color
            bg = self.selected_bg if i == self.selectedIndex else self.bg_color
            renderer.draw_text(absolute_x + 1, absolute_y + 1 + i, txt[:inner_w].ljust(inner_w), fg, bg)
            if mn:
                mpos = pos
                if mpos < 0:
                    try:
                        mpos = label.lower().index(mn)
                    except ValueError:
                        mpos = -1
                if mpos >= 0:
                    try:
                        hotkey_fg = self.hotkey_selected_fg if i == self.selectedIndex else self.hotkey_fg
                        hotkey_bg = self.hotkey_selected_bg if i == self.selectedIndex else self.hotkey_bg
                        _safe_add_string(renderer.screen, absolute_y + 1 + i, absolute_x + 1 + mpos, label[mpos], renderer.get_color_pair(hotkey_fg, hotkey_bg) | curses.A_BOLD)
                    except curses.error:
                        pass

    def open(self):
        self.opened = True

    def close(self):
        self.opened = False

    def handleEvent(self, event: UIEvent) -> bool:
        if not self.opened:
            return False
        if event.type == "key":
            key = event.data.get('key')
            if key == curses.KEY_UP:
                self.selectedIndex = (self.selectedIndex - 1) % len(self.items)
                return True
            if key == curses.KEY_DOWN:
                self.selectedIndex = (self.selectedIndex + 1) % len(self.items)
                return True
            if key in (KEY_ENTER,):
                item = self.items[self.selectedIndex]
                self.close()
                if item.callback and item.enabled:
                    item.callback()
                return True
            if key == KEY_ESC:
                self.close()
                return True
        if event.type == "mouse":
            mouse_x, mouse_y = event.data['x'], event.data['y']
            absolute_x, absolute_y = self.get_absolute_position()
            if mouse_x >= absolute_x and mouse_x < absolute_x + self.width and mouse_y >= absolute_y and mouse_y < absolute_y + self.height:
                idx = mouse_y - (absolute_y + 1)
                if 0 <= idx < len(self.items):
                    self.selectedIndex = idx
                    if event.data.get('bstate', 0) & curses.BUTTON1_PRESSED:
                        self.close()
                        item = self.items[idx]
                        if item.callback and item.enabled:
                            item.callback()
                        return True
                return True
            else:
                self.close()
                return True
        return False
