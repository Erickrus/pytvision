import curses
from typing import List, Optional, Callable, Dict

from .terminal_renderer import TerminalRenderer
from .ui_event import UIEvent



class Component:
    DEFAULT_FG = curses.COLOR_WHITE
    DEFAULT_BG = -1  # Default terminal background

    def __init__(self, left: int = 0, top: int = 0, width: int = 10, height: int = 3, parent=None):
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.parent = parent
        self.visibility = True
        self.isFocused = False
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.fg_color = self.DEFAULT_FG
        self.bg_color = self.DEFAULT_BG

    def set_colors(self, fg: Optional[int] = None, bg: Optional[int] = None):
        if fg is not None:
            self.fg_color = fg
        if bg is not None:
            self.bg_color = bg

    def get_absolute_position(self):
        absolute_x, absolute_y = self.left, self.top
        p = self.parent
        while p:
            absolute_x += p.left
            absolute_y += p.top
            p = p.parent
        return absolute_x, absolute_y

    def render(self, renderer: TerminalRenderer):
        raise NotImplementedError

    def handleEvent(self, event: UIEvent) -> bool:
        return False

    def show(self):
        self.visibility = True

    def hide(self):
        self.visibility = False

    def addEventListener(self, evname: str, callback: Callable):
        self.event_handlers.setdefault(evname, []).append(callback)

    def dispatchEvent(self, evname: str, **kw):
        event = UIEvent(evname, **kw)
        for callback in list(self.event_handlers.get(evname, [])):
            try:
                callback(event)
            except Exception:
                pass

def is_mouse_over(child: Component, mouse_x: int, mouse_y: int):
    absolute_x, absolute_y = child.get_absolute_position()
    return (mouse_x >= absolute_x and mouse_x < absolute_x + child.width and mouse_y >= absolute_y and mouse_y < absolute_y + child.height)
