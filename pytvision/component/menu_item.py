import curses
from typing import List, Optional, Callable

from .component import Component
from .terminal_renderer import TerminalRenderer
from .ui_event import UIEvent

from ..utils import _split_mnemonic, _safe_add_string, KEY_ENTER, KEY_ESC

class MenuItem:
    def __init__(self, id_, label, callback: Optional[Callable] = None, shortcut: Optional[str] = None, enabled=True, submenu=None):
        self.id = id_
        self.label = label
        self.callback = callback
        self.shortcut = shortcut
        self.enabled = enabled
        self.submenu = submenu
