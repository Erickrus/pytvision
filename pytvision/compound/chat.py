
import curses
import textwrap

from ..component.component import Component, is_mouse_over
from ..component.terminal_renderer import TerminalRenderer
from ..component.ui_event import UIEvent
from ..component.text_area import TextArea
from ..component.button import Button

from ..utils import _safe_add_string


class Chat(Component):
    DEFAULT_FG = curses.COLOR_BLACK
    DEFAULT_BG = curses.COLOR_WHITE
    DEFAULT_BORDER_FG = curses.COLOR_BLACK
    DEFAULT_BORDER_BG = 20
    DEFAULT_MESSAGE_FG = curses.COLOR_BLACK
    DEFAULT_MESSAGE_BG_LEFT = curses.COLOR_CYAN  # Bubble background for "Friend"
    DEFAULT_MESSAGE_BG_RIGHT = curses.COLOR_GREEN  # Bubble background for "Me"
    DEFAULT_INPUT_FG = curses.COLOR_WHITE
    DEFAULT_INPUT_BG = curses.COLOR_BLUE
    DEFAULT_BUTTON_FG = curses.COLOR_BLACK
    DEFAULT_BUTTON_BG = curses.COLOR_GREEN

    def __init__(self, left, top, width, height, parent=None):
        super().__init__(left, top, width, height, parent)
        self.messages = []  # List of (sender, message) tuples
        self.input = TextArea(1, height - 4, width - 12, 3, parent=self)  # 3-line TextArea
        self.send_button = Button(width - 10, height - 3, 8, "Send", parent=self, onclick=self.on_send)
        self.fg_color = self.DEFAULT_FG
        self.bg_color = self.DEFAULT_BG
        self.border_fg = self.DEFAULT_BORDER_FG
        self.border_bg = self.DEFAULT_BORDER_BG
        self.message_fg = self.DEFAULT_MESSAGE_FG
        self.message_bg_left = self.DEFAULT_MESSAGE_BG_LEFT
        self.message_bg_right = self.DEFAULT_MESSAGE_BG_RIGHT
        self.input.set_colors(self.DEFAULT_INPUT_FG, self.DEFAULT_INPUT_BG)
        self.send_button.set_colors(self.DEFAULT_BUTTON_FG, self.DEFAULT_BUTTON_BG)

    def on_send(self):
        msg = self.input.get_value().strip()
        if msg:
            self.messages.append(("Me", msg))
            self.input.set_value("")
            self.dispatchEvent("onsend", message=msg)

    def add_message(self, sender: str, message: str):
        self.messages.append((sender, message))

    def render(self, renderer: TerminalRenderer):
        if not self.visibility:
            return
        absolute_x, absolute_y = self.get_absolute_position()
        renderer.draw_box(absolute_x, absolute_y, self.width, self.height, fg=self.border_fg, bg=self.border_bg, border_style="single")
        inner_h = self.height - 5  # Space for 3-line input and button
        inner_w = self.width - 2
        max_bubble_w = inner_w - 6  # Maximum bubble width
        # Prepare messages with wrapped lines
        wrapped_messages = []
        for sender, msg in self.messages:
            # Wrap text to fit within max_bubble_w - 2 (for '│ │')
            wrapped = textwrap.wrap(msg, width=max_bubble_w - 2) or [""]
            wrapped_messages.append((sender, wrapped))
        
        # Calculate rows needed: 2 borders + len(wrapped) text lines + 1 empty row per message
        rendered_messages = []
        for sender, lines in wrapped_messages:
            rows_needed = 2 + len(lines)  # Top/bottom borders + text lines
            rendered_messages.append((sender, lines, rows_needed))
        
        # Determine which messages to display (newest at bottom)
        total_rows_needed = sum(rows + 1 for _, _, rows in rendered_messages)  # +1 for empty row
        start_idx = 0
        current_rows = 0
        for i in range(len(rendered_messages) - 1, -1, -1):
            rows = rendered_messages[i][2] + 1
            if current_rows + rows <= inner_h:
                current_rows += rows
                start_idx = i
            else:
                break
        
        # Render messages
        current_y = absolute_y + inner_h - current_rows
        for sender, lines, _ in rendered_messages[start_idx:]:
            if current_y + len(lines) + 2 > absolute_y + inner_h:
                break
            # Find the longest line to set bubble width
            bubble_w = min(max_bubble_w, max(len(f" {line} ") for line in lines) + 2)
            if sender == "Me":
                x_offset = inner_w - bubble_w
                bg = self.message_bg_right
            else:
                x_offset = 2
                bg = self.message_bg_left
            # Draw top border
            _safe_add_string(renderer.screen, current_y, absolute_x + x_offset, "╭" + "─" * (bubble_w - 2) + "╮", renderer.get_color_pair(self.message_fg, bg))
            # Draw text lines
            for i, line in enumerate(lines):
                padded_text = f" {line} ".ljust(bubble_w - 2)
                _safe_add_string(renderer.screen, current_y + 1 + i, absolute_x + x_offset, "│" + padded_text + "│", renderer.get_color_pair(self.message_fg, bg))
            # Draw bottom border
            _safe_add_string(renderer.screen, current_y + 1 + len(lines), absolute_x + x_offset, "╰" + "─" * (bubble_w - 2) + "╯", renderer.get_color_pair(self.message_fg, bg))
            current_y += len(lines) + 3  # Text lines + borders + empty row
        
        self.input.render(renderer)
        self.send_button.render(renderer)

    def handleEvent(self, event: UIEvent) -> bool:
        if self.input.handleEvent(event):
            return True
        if self.send_button.handleEvent(event):
            return True
        if event.type == "mouse":
            mouse_x, mouse_y = event.data['x'], event.data['y']
            if is_mouse_over(self, mouse_x, mouse_y):
                self.isFocused = True
                return True
        return False