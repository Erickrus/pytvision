
import curses
from typing import List, Optional, Tuple

from .component import Component, is_mouse_over
from .terminal_renderer import TerminalRenderer
from .ui_event import UIEvent
from ..utils import _safe_add_string, _clamp, _split_mnemonic, KEY_TAB, KEY_ENTER, KEY_ESC

from .label import Label
from .input import Input
from .text_area import TextArea
from .multi_list import MultiList
from .password import Password
from .button import Button
from .dropdown import Dropdown
from .context_menu import ContextMenu



class WindowManager:
    def __init__(self):
        self.windows: List['Window'] = []
        self.modal_stack: List['Window'] = []
        self.main_menu: Optional['MainMenuBar'] = None
        self.desktop_is_active = False

    def add(self, window: 'Window'):
        if window in self.windows:
            self.windows.remove(window)
        self.windows.append(window)
        window.manager = self
        self.desktop_is_active = False

    def remove(self, window: 'Window'):
        if window in self.windows:
            self.windows.remove(window)
        if window in self.modal_stack:
            self.modal_stack.remove(window)
        self.desktop_is_active = not self.windows

    def top(self) -> Optional['Window']:
        return self.windows[-1] if self.windows else None

    def bring_to_top(self, window: 'Window'):
        if window in self.windows:
            self.windows.remove(window)
        self.windows.append(window)
        self.desktop_is_active = False

    def push_modal(self, window: 'Window'):
        self.add(window)
        self.modal_stack.append(window)
        self.bring_to_top(window)
        if self.main_menu:
            self.main_menu.active_index = None

    def pop_modal(self):
        if self.modal_stack:
            self.modal_stack.pop()
    def handle_event(self, event: UIEvent) -> bool:
        if self.modal_stack:
            return self.modal_stack[-1].handleEvent(event)
        if event.type == "key":
            # First try the focused component in the topmost window
            active_window = self.top()
            if active_window and not self.desktop_is_active:
                for child in active_window.children:
                    if getattr(child, "isFocused", False) and child.handleEvent(event):
                        return True
            # Handle Tab key for cycling focus
            if event.data.get('key') == KEY_TAB:
                if active_window and not self.desktop_is_active:
                    active_window.cycle_focus()
                    return True
            # Then try the main menu
            if self.main_menu:
                return self.main_menu.handleEvent(event)
        if event.type == "mouse":
            mouse_x, mouse_y = event.data['x'], event.data['y']
            bstate = event.data.get('bstate', 0)
            if self.main_menu and self.main_menu.handleEvent(event):
                return True
            for window in reversed(self.windows):
                if not window.visibility:
                    continue
                if window.contains(mouse_x, mouse_y):
                    if bstate & (curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED):
                        self.bring_to_top(window)
                    return window.handleEvent(event)
            if bstate & curses.BUTTON1_PRESSED:
                self.desktop_is_active = True
                if self.main_menu:
                    self.main_menu.active_index = None
                return True
        return False

    def render_all(self, renderer: TerminalRenderer):
        bg_char = '░'
        try:
            for row in range(renderer.h):
                renderer.screen.addstr(row, 0, bg_char * renderer.w, renderer.get_color_pair(curses.COLOR_WHITE, curses.COLOR_BLUE))
        except curses.error:
            pass
        for i, window in enumerate(self.windows):
            if window.visibility:
                window.isFocused = (i == len(self.windows) - 1) and not self.desktop_is_active
                window.render(renderer)
        if self.main_menu:
            self.main_menu.render(renderer)

class Window(Component):
    DEFAULT_FG = curses.COLOR_WHITE
    DEFAULT_BG = curses.COLOR_BLACK
    DEFAULT_BORDER_FG_FOCUSED = 21
    DEFAULT_BORDER_BG_FOCUSED = 20
    DEFAULT_BORDER_FG_UNFOCUSED = curses.COLOR_BLACK
    DEFAULT_BORDER_BG_UNFOCUSED = 20
    DEFAULT_TITLE_FG_FOCUSED = 21
    DEFAULT_TITLE_BG_FOCUSED = 20
    DEFAULT_TITLE_FG_UNFOCUSED = curses.COLOR_BLACK
    DEFAULT_TITLE_BG_UNFOCUSED = 20
    DEFAULT_CLOSE_FG = curses.COLOR_GREEN
    DEFAULT_CLOSE_BG = 20

    def __init__(self, left, top, width, height, title: str = "Window", parent=None, modal=False):
        super().__init__(left, top, width, height, parent)
        self.title = title
        self.children: List[Component] = []
        self.has_shadow = True
        self.modal = modal
        self.dragging = False
        self._dragoff = (0, 0)
        self.manager = None
        self.border_fg_focused = self.DEFAULT_BORDER_FG_FOCUSED
        self.border_bg_focused = self.DEFAULT_BORDER_BG_FOCUSED
        self.border_fg_unfocused = self.DEFAULT_BORDER_FG_UNFOCUSED
        self.border_bg_unfocused = self.DEFAULT_BORDER_BG_UNFOCUSED
        self.title_fg_focused = self.DEFAULT_TITLE_FG_FOCUSED
        self.title_bg_focused = self.DEFAULT_TITLE_BG_FOCUSED
        self.title_fg_unfocused = self.DEFAULT_TITLE_FG_UNFOCUSED
        self.title_bg_unfocused = self.DEFAULT_TITLE_BG_UNFOCUSED
        self.close_fg = self.DEFAULT_CLOSE_FG
        self.close_bg = self.DEFAULT_CLOSE_BG

    def set_border_colors(self, fg_focused=None, bg_focused=None, fg_unfocused=None, bg_unfocused=None):
        if fg_focused is not None:
            self.border_fg_focused = fg_focused
        if bg_focused is not None:
            self.border_bg_focused = bg_focused
        if fg_unfocused is not None:
            self.border_fg_unfocused = fg_unfocused
        if bg_unfocused is not None:
            self.border_bg_unfocused = bg_unfocused

    def set_title_colors(self, fg_focused=None, bg_focused=None, fg_unfocused=None, bg_unfocused=None):
        if fg_focused is not None:
            self.title_fg_focused = fg_focused
        if bg_focused is not None:
            self.title_bg_focused = bg_focused
        if fg_unfocused is not None:
            self.title_fg_unfocused = fg_unfocused
        if bg_unfocused is not None:
            self.title_bg_unfocused = bg_unfocused

    def set_close_button_colors(self, fg=None, bg=None):
        if fg is not None:
            self.close_fg = fg
        if bg is not None:
            self.close_bg = bg

    def add(self, child: Component):
        child.parent = self
        self.children.append(child)

    def render(self, renderer: TerminalRenderer):
        if not self.visibility:
            return
        absolute_x, absolute_y = self.get_absolute_position()
        border_fg = self.border_fg_focused if self.isFocused else self.border_fg_unfocused
        border_bg = self.border_bg_focused if self.isFocused else self.border_bg_unfocused
        title_fg = self.title_fg_focused if self.isFocused else self.title_fg_unfocused
        title_bg = self.title_bg_focused if self.isFocused else self.title_bg_unfocused
        bg_attr = renderer.get_color_pair(self.fg_color, self.bg_color)
        for r in range(1, self.height - 1):
            _safe_add_string(renderer.screen, absolute_y + r, absolute_x + 1, ' ' * (self.width - 2), bg_attr)
        renderer.draw_box(absolute_x, absolute_y, self.width, self.height, title=None, win=renderer.screen, fg=border_fg, bg=border_bg, border_style="double")
        _safe_add_string(renderer.screen, absolute_y, absolute_x + 1, "[", renderer.get_color_pair(border_fg, border_bg))
        _safe_add_string(renderer.screen, absolute_y, absolute_x + 2, "■", renderer.get_color_pair(self.close_fg, self.close_bg))
        _safe_add_string(renderer.screen, absolute_y, absolute_x + 3, "]", renderer.get_color_pair(border_fg, border_bg))
        title_text = f" {self.title} "
        title_x = absolute_x + (self.width - len(title_text)) // 2
        _safe_add_string(renderer.screen, absolute_y, title_x, title_text, renderer.get_color_pair(title_fg, title_bg) | curses.A_BOLD)
        status_label = next((child for child in self.children if isinstance(child, Label) and child.top == self.height - 2), None)
        if status_label:
            status_text = status_label.text.center(self.width - 2)
            _safe_add_string(renderer.screen, absolute_y + self.height - 1, absolute_x + 1, status_text, renderer.get_color_pair(title_fg, title_bg))
        if self.has_shadow:
            renderer.draw_shadow(absolute_x, absolute_y, self.width, self.height, win=renderer.screen)
        for child in self.children:
            if child.visibility and child != status_label:
                child.render(renderer)

    def contains(self, mouse_x, mouse_y):
        absolute_x, absolute_y = self.get_absolute_position()
        return (mouse_x >= absolute_x and mouse_x < absolute_x + self.width and mouse_y >= absolute_y and mouse_y < absolute_y + self.height)

    def unfocus_children(self):
        for child in self.children:
            if hasattr(child, 'isFocused'):
                child.isFocused = False

    def collect_focusables(self):
        out = []
        for child in self.children:
            if isinstance(child, (Input, TextArea, MultiList, Password, Button)):
                out.append(child)
        return out

    def cycle_focus(self):
        focusable_components = self.collect_focusables()
        if not focusable_components:
            return
        current_index = next((i for i, child in enumerate(focusable_components) if getattr(child, 'isFocused', False)), None)
        if current_index is not None:
            focusable_components[current_index].isFocused = False
            next_index = (current_index + 1) % len(focusable_components)
            focusable_components[next_index].isFocused = True
        elif focusable_components:
            focusable_components[0].isFocused = True

    def handleEvent(self, event: UIEvent) -> bool:
        if event.type == "mouse":
            mouse_x, mouse_y = event.data['x'], event.data['y']
            bstate = event.data.get('bstate', 0)
            absolute_x, absolute_y = self.get_absolute_position()
            if self.dragging and event.data.get('etype') == 'motion' and bstate & curses.REPORT_MOUSE_POSITION:
                dx = mouse_x - self._dragoff[0]
                dy = mouse_y - self._dragoff[1]
                self.left = _clamp(dx, 0, max(0, event.data.get('screen_w', 100) - self.width))
                self.top = _clamp(dy, 0, max(0, event.data.get('screen_h', 40) - self.height))
                return True
            if bstate & curses.BUTTON1_RELEASED:
                self.dragging = False
                return True
            if bstate & curses.BUTTON1_PRESSED:
                if mouse_y == absolute_y and absolute_x <= mouse_x < absolute_x + self.width:
                    if mouse_x >= absolute_x + 1 and mouse_x <= absolute_x + 3:
                        if self.manager:
                            self.manager.remove(self)
                        return True
                    else:
                        self.dragging = True
                        self._dragoff = (mouse_x - absolute_x, mouse_y - absolute_y)
                        self.manager.bring_to_top(self)
                        return True
                for child in reversed(self.children):
                    if child.visibility and isinstance(child, Dropdown):
                        ax_c, ay_c = child.get_absolute_position()
                        effective_h = child.dropdown_height if child.dropdown_open else child.height
                        if mouse_x >= ax_c and mouse_x < ax_c + child.width and mouse_y >= ay_c and mouse_y < ay_c + effective_h:
                            if child.handleEvent(event):
                                return True
                for child in reversed(self.children):
                    if child.visibility and is_mouse_over(child, mouse_x, mouse_y) and not isinstance(child, Dropdown):
                        if child.handleEvent(event):
                            return True
                self.unfocus_children()
                return True
        elif event.type == "key":
            for child in self.children:
                if getattr(child, "isFocused", False):
                    if child.handleEvent(event):
                        return True
            return False
        return False
    
class MainMenuBar:
    DEFAULT_FG = curses.COLOR_BLACK
    DEFAULT_BG = 20
    DEFAULT_SELECTED_FG = curses.COLOR_BLACK
    DEFAULT_SELECTED_BG = curses.COLOR_GREEN
    DEFAULT_HOTKEY_FG = curses.COLOR_RED
    DEFAULT_HOTKEY_BG = 20
    DEFAULT_HOTKEY_SELECTED_FG = curses.COLOR_RED
    DEFAULT_HOTKEY_SELECTED_BG = curses.COLOR_GREEN

    def __init__(self, manager: WindowManager, items: List[Tuple[str, ContextMenu]]):
        self.manager = manager
        self.items = items
        self.active_index: Optional[int] = None
        self.layouts: List[Tuple[int, int, str]] = []
        self.top = 0
        self.height = 1
        self.fg_color = self.DEFAULT_FG
        self.bg_color = self.DEFAULT_BG
        self.selected_fg = self.DEFAULT_SELECTED_FG
        self.selected_bg = self.DEFAULT_SELECTED_BG
        self.hotkey_fg = self.DEFAULT_HOTKEY_FG
        self.hotkey_bg = self.DEFAULT_HOTKEY_BG
        self.hotkey_selected_fg = self.DEFAULT_HOTKEY_SELECTED_FG
        self.hotkey_selected_bg = self.DEFAULT_HOTKEY_SELECTED_BG

    def set_colors(self, fg=None, bg=None):
        if fg is not None:
            self.fg_color = fg
        if bg is not None:
            self.bg_color = bg

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

    def render(self, renderer: TerminalRenderer):
        _safe_add_string(renderer.screen, self.top, 0, " " * renderer.w, renderer.get_color_pair(self.fg_color, self.bg_color))
        x = 1
        self.layouts = []
        for idx, (label, menu) in enumerate(self.items):
            disp, mn, pos = _split_mnemonic(label)
            txt = f" {disp} "
            fg = self.selected_fg if self.active_index == idx else self.fg_color
            bg = self.selected_bg if self.active_index == idx else self.bg_color
            _safe_add_string(renderer.screen, self.top, x, txt, renderer.get_color_pair(fg, bg))
            if mn:
                loc = pos if pos >= 0 else disp.lower().find(mn)
                if loc != -1:
                    char_to_underline = disp[loc]
                    hotkey_fg = self.hotkey_selected_fg if self.active_index == idx else self.hotkey_fg
                    hotkey_bg = self.hotkey_selected_bg if self.active_index == idx else self.hotkey_bg
                    _safe_add_string(renderer.screen, self.top, x + 1 + loc, char_to_underline, renderer.get_color_pair(hotkey_fg, hotkey_bg) | curses.A_BOLD)
            self.layouts.append((x, len(txt), disp))
            x += len(txt) + 1
        if self.active_index is not None and 0 <= self.active_index < len(self.items):
            _, menu = self.items[self.active_index]
            lx, _, _ = self.layouts[self.active_index]
            menu.left = lx
            menu.top = 1
            menu.parent = None
            menu.open()
            menu.render(renderer)

    def handleEvent(self, event: UIEvent) -> bool:
        if event.type == "key":
            key = event.data.get('key')
            if key == KEY_ESC:
                if self.active_index is not None:
                    self.items[self.active_index][1].close()
                    self.active_index = None
                    return True
            if key in (curses.KEY_LEFT, curses.KEY_RIGHT):
                if self.active_index is None:
                    self.active_index = 0
                else:
                    self.items[self.active_index][1].close()
                    if key == curses.KEY_LEFT:
                        self.active_index = (self.active_index - 1 + len(self.items)) % len(self.items)
                    else:
                        self.active_index = (self.active_index + 1) % len(self.items)
                self.items[self.active_index][1].open()
                return True
            if key in (curses.KEY_DOWN, KEY_ENTER):
                if self.active_index is None:
                    self.active_index = 0
                menu = self.items[self.active_index][1]
                if not menu.opened:
                    menu.open()
                return menu.handleEvent(event)
            if isinstance(key, tuple) and key[0] == "ALT":
                alt_key = key[1]
                if alt_key in (ord('f'), ord('F')):
                    self.active_index = 0
                    self.items[self.active_index][1].open()
                    return True
                elif alt_key in (ord('w'), ord('W')):
                    self.active_index = 1
                    self.items[self.active_index][1].open()
                    return True
                elif alt_key in (ord('h'), ord('H')):
                    self.active_index = 2
                    self.items[self.active_index][1].open()
                    return True
        if event.type == "mouse":
            mouse_x, mouse_y = event.data['x'], event.data['y']
            if mouse_y == self.top:
                rx = mouse_x
                for idx, (lx, lw, _) in enumerate(self.layouts):
                    if rx >= lx and rx < lx + lw:
                        if self.active_index == idx:
                            self.items[self.active_index][1].close()
                            self.active_index = None
                        else:
                            if self.active_index is not None:
                                self.items[self.active_index][1].close()
                            self.active_index = idx
                        return True
            if self.active_index is not None:
                menu = self.items[self.active_index][1]
                if menu.handleEvent(event):
                    if not menu.opened:
                        self.active_index = None
                    return True
        return False
