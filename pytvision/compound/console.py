
import curses
import time
import threading
import queue

from ..component.component import Component, is_mouse_over
from ..component.terminal_renderer import TerminalRenderer
from ..component.ui_event import UIEvent
from ..utils import _safe_add_string

class Console(Component):
    DEFAULT_FG = curses.COLOR_WHITE
    DEFAULT_BG = curses.COLOR_BLACK
    DEFAULT_BORDER_FG = curses.COLOR_BLACK
    DEFAULT_BORDER_BG = 20  # Light gray
    DEFAULT_SCROLLBAR_FG = curses.COLOR_WHITE
    DEFAULT_SCROLLBAR_BG = 20

    def __init__(self, left, top, width, height, parent=None):
        super().__init__(left, top, width, height, parent)
        self.lines = []
        self.view_top = 0
        self.queue = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self.read_process, daemon=True)
        self.thread.start()
        self.fg_color = self.DEFAULT_FG
        self.bg_color = self.DEFAULT_BG
        self.border_fg = self.DEFAULT_BORDER_FG
        self.border_bg = self.DEFAULT_BORDER_BG
        self.scrollbar_fg = self.DEFAULT_SCROLLBAR_FG
        self.scrollbar_bg = self.DEFAULT_SCROLLBAR_BG

    def read_process(self):
        # Simulate an external process outputting lines
        counter = 0
        while self.running:
            self.queue.put(f"Log message {counter}")
            counter += 1
            time.sleep(1)

    def append_line(self, line: str):
        self.lines.append(line)
        inner_h = self.height - 2
        if len(self.lines) > inner_h:
            self.view_top = len(self.lines) - inner_h

    def stop(self):
        self.running = False
        self.thread.join()

    def render(self, renderer: TerminalRenderer):
        if not self.visibility:
            return
        absolute_x, absolute_y = self.get_absolute_position()
        renderer.draw_box(absolute_x, absolute_y, self.width, self.height, title=None, fg=self.border_fg, bg=self.border_bg, border_style="single")
        inner_h = self.height - 2
        inner_w = self.width - 2
        has_scrollbar = len(self.lines) > inner_h
        text_w = inner_w - 1 if has_scrollbar else inner_w
        while not self.queue.empty():
            self.append_line(self.queue.get())
        for i in range(inner_h):
            idx = self.view_top + i
            if idx < len(self.lines):
                renderer.draw_text(absolute_x + 1, absolute_y + 1 + i, self.lines[idx][:text_w].ljust(text_w), self.fg_color, self.bg_color)
            else:
                renderer.draw_text(absolute_x + 1, absolute_y + 1 + i, " " * text_w, self.fg_color, self.bg_color)
        if has_scrollbar:
            sbar_x = absolute_x + self.width - 2
            scrollbar_attr = renderer.get_color_pair(self.scrollbar_fg, self.scrollbar_bg)
            for i in range(inner_h):
                _safe_add_string(renderer.screen, absolute_y + 1 + i, sbar_x, '│', scrollbar_attr)
            thumb_size = max(1, inner_h * inner_h // len(self.lines))
            thumb_pos = inner_h * self.view_top // len(self.lines)
            for i in range(thumb_size):
                _safe_add_string(renderer.screen, absolute_y + 1 + thumb_pos + i, sbar_x, '█', scrollbar_attr)

    def handleEvent(self, event: UIEvent) -> bool:
        if event.type == "key":
            key = event.data.get('key')
            inner_h = self.height - 2
            if key == curses.KEY_UP:
                self.view_top = max(0, self.view_top - 1)
                return True
            if key == curses.KEY_DOWN:
                self.view_top = min(max(0, len(self.lines) - inner_h), self.view_top + 1)
                return True
            if key == curses.KEY_PPAGE:
                self.view_top = max(0, self.view_top - inner_h)
                return True
            if key == curses.KEY_NPAGE:
                self.view_top = min(max(0, len(self.lines) - inner_h), self.view_top + inner_h)
                return True
        if event.type == "mouse":
            mouse_x, mouse_y = event.data['x'], event.data['y']
            if is_mouse_over(self, mouse_x, mouse_y):
                self.isFocused = True
                inner_h = self.height - 2
                if mouse_x == self.get_absolute_position()[0] + self.width - 2:
                    thumb_size = max(1, inner_h * inner_h // len(self.lines))
                    thumb_pos = inner_h * self.view_top // len(self.lines)
                    if mouse_y >= self.get_absolute_position()[1] + 1 + thumb_pos and mouse_y < self.get_absolute_position()[1] + 1 + thumb_pos + thumb_size:
                        return True
                    elif mouse_y < self.get_absolute_position()[1] + 1 + thumb_pos:
                        self.view_top = max(0, self.view_top - inner_h)
                        return True
                    elif mouse_y >= self.get_absolute_position()[1] + 1 + thumb_pos + thumb_size:
                        self.view_top = min(max(0, len(self.lines) - inner_h), self.view_top + inner_h)
                        return True
                return True
        return False
