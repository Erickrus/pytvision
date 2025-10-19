import curses
import os
import sys
import time
import locale

from pytvision.utils import KEY_ESC, KEY_ENTER, KEY_TAB, KEY_BACKSPACE

from pytvision.component.terminal_renderer import TerminalRenderer
from pytvision.component.window import Window, WindowManager, MainMenuBar
from pytvision.component.dropdown import Dropdown
from pytvision.component.text_area import TextArea
from pytvision.component.label import Label
from pytvision.component.button import Button
from pytvision.component.context_menu import ContextMenu
from pytvision.component.menu_item import MenuItem
from pytvision.component.modal import Modal
from pytvision.component.ui_event import UIEvent
from pytvision.compound.confirm_modal import ConfirmModal
from pytvision.compound.notification_modal import NotificationModal
from pytvision.compound.open_dialog import OpenDialog
from pytvision.compound.save_dialog import SaveDialog
from pytvision.compound.chat import Chat
from pytvision.compound.console import Console


class DemoApp:
    def __init__(self, screen):
        self.screen = screen
        self.renderer = TerminalRenderer(screen)
        self.manager = WindowManager()
        self.manager.main_menu = None
        self.running = True
        self.build()

    def build(self):
        h, w = self.screen.getmaxyx()
        # Main application window (unchanged)
        appwin = Window(2, 2, max(60, w - 6), max(20, h - 6), title="PyTVision - Demo", parent=None)
        files = sorted(os.listdir("."))[:50]
        filelist = Dropdown(2, 2, 28, files, parent=appwin)
        appwin.add(filelist)
        editor = TextArea(31, 2, appwin.width - 33, 14, parent=appwin, value="Welcome to PyTVision!\nType and try Alt+F to open menu.")
        appwin.add(editor)
        ok = Button(appwin.width - 20, 17, 8, "OK", parent=appwin, window=appwin, onclick=lambda: self.on_ok(editor))
        cancel = Button(appwin.width - 10, 17, 8, "Quit", parent=appwin, window=appwin, onclick=self.exit)
        appwin.add(ok)
        appwin.add(cancel)
        status = Label(1, appwin.height - 2, appwin.width - 2, 1, text="Ready. Alt+F File | Alt-W Window | Alt-H Help")
        appwin.add(status)
        self.status_label = status
        self.manager.add(appwin)
        self.appwin = appwin
        self.filelist = filelist
        self.editor = editor

        # Console window
        consolewin = Window(10, 5, 34, 12, title="Console Demo", parent=None)
        console = Console(2, 2, 30, 8, parent=consolewin)
        consolewin.add(console)
        self.manager.add(consolewin)
        self.consolewin = consolewin
        self.console = console

        # confirm_button = Button(2, 17, 14, "Show Confirm", parent=chatwin, onclick=lambda: self.show_confirm(chat))
        # notify_button = Button(18, 17, 14, "Show Notify", parent=chatwin, onclick=self.show_notification)
        # chatwin.add(confirm_button)
        # chatwin.add(notify_button)

        # Chat window
        chatwin = Window(20, 5, 60, 20, title="Chat Demo", parent=None)
        chat = Chat(2, 2, 56, 16, parent=chatwin)
        chat.add_message("Friend", "Hello! How are you?")
        
        chatwin.add(chat)

        self.manager.add(chatwin)
        self.chatwin = chatwin
        self.chat = chat

        # Menu setup
        filemenu = ContextMenu(0, 1, 28)
        filemenu.add(MenuItem("open", "&Open", callback=self.open_file))
        filemenu.add(MenuItem("save", "&Save", callback=self.save_file))
        filemenu.add(MenuItem("sep", "-" * 10, callback=None, enabled=False))
        filemenu.add(MenuItem("exit", "E&xit", callback=self.exit))
        winmenu = ContextMenu(0, 1, 22)
        winmenu.add(MenuItem("min", "&Minimize", callback=lambda: None))
        winmenu.add(MenuItem("close", "&Close", callback=lambda: self.manager.remove(self.appwin)))
        helpmenu = ContextMenu(0, 1, 20)
        helpmenu.add(MenuItem("about", "&About", callback=self.show_about))
        mbar = MainMenuBar(self.manager, [("&File", filemenu), ("&Window", winmenu), ("&Help", helpmenu)])
        self.manager.main_menu = mbar

    def on_ok(self, editor: TextArea):
        try:
            selected_file = self.filelist.get_value()
            self.status_label.text = f"OK: {selected_file or 'No file selected'}, {len(editor.get_value().splitlines())} lines"
        except:
            import traceback
            traceback.print_exc()

    def show_about(self):
        m = Modal(40, 10, "About", parent=self.appwin)
        lbl = Label(2, 2, 36, 4, text="PyTVision Prototype (c) 2025\nMinimal demo.")
        btn = Button(14, 6, 12, "Close", parent=m, window=m, onclick=lambda: m.manager.remove(m))
        m.add(lbl)
        m.add(btn)
        self.manager.add(m)
        self.manager.push_modal(m)

    def show_confirm(self, chat: Chat):
        def on_confirm():
            chat.add_message("Friend", "Confirmed! Thanks!")
        m = ConfirmModal("Do you want to confirm this action?", parent=self.chatwin, on_confirm=on_confirm)
        self.manager.add(m)
        self.manager.push_modal(m)

    def show_notification(self):
        m = NotificationModal("This is a notification!", parent=self.chatwin)
        self.manager.add(m)
        self.manager.push_modal(m)

    def open_file(self):
        def callback(path):
            try:
                with open(path, "r") as f:
                    self.editor.set_value(f.read())
                    self.status_label.text = f"Opened: {path}"
            except Exception as e:
                self.status_label.text = f"Error: {str(e)}"
        dialog = OpenDialog(self.appwin, callback)
        dialog.addEventListener("onerror", lambda e: setattr(self.status_label, 'text', e.data['message']))
        self.manager.add(dialog)
        self.manager.push_modal(dialog)

    def save_file(self):
        def callback(path):
            try:
                with open(path, "w") as f:
                    f.write(self.editor.get_value())
                    self.status_label.text = f"Saved: {path}"
            except Exception as e:
                self.status_label.text = f"Error: {str(e)}"
        dialog = SaveDialog(self.appwin, callback=callback)
        dialog.addEventListener("onerror", lambda e: setattr(self.status_label, 'text', e.data['message']))
        self.manager.add(dialog)
        self.manager.push_modal(dialog)

    def exit(self):
        self.console.stop()
        self.running = False

    def parse_mouse(self, mouse_event_data):
        _, mx, my, _, bstate = mouse_event_data
        etype = 'click'
        if bstate & curses.REPORT_MOUSE_POSITION:
            etype = 'motion'
        return UIEvent("mouse", x=mx, y=my, bstate=bstate, etype=etype,
                       screen_w=self.renderer.w, screen_h=self.renderer.h)

    def handle_alt(self, event):
        if event.type == "key" and isinstance(event.data.get('key'), tuple) and event.data['key'][0] == "ALT":
            key = event.data['key'][1]
            if key in (ord('f'), ord('F')):
                if self.manager.main_menu:
                    self.manager.main_menu.active_index = 0
                    return True
            elif key in (ord('w'), ord('W')):
                if self.manager.main_menu:
                    self.manager.main_menu.active_index = 1
                    return True
            elif key in (ord('h'), ord('H')):
                if self.manager.main_menu:
                    self.manager.main_menu.active_index = 2
                    return True
        return False

    def mainloop(self):
        self.screen.nodelay(False)
        locale.setlocale(locale.LC_ALL, '')
        self.screen.keypad(True)
        curses.curs_set(0)
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        curses.mouseinterval(0)
        while self.running:
            self.renderer.refresh_dimensions()
            self.screen.erase()
            for r in range(self.renderer.h):
                try:
                    ch = ' ' if (r % 2 == 0) else ' '
                    self.screen.addstr(r, 0, ch * (self.renderer.w), self.renderer.get_color_pair(curses.COLOR_WHITE, -1))
                except curses.error:
                    pass
            self.manager.render_all(self.renderer)
            self.screen.refresh()
            try:
                key = self.screen.get_wch()
            except curses.error:
                time.sleep(0.01)
                continue
            if isinstance(key, str):
                if ord(key) == 27:
                    event = UIEvent("key", key=KEY_ESC)
                    self.manager.handle_event(event)
                elif key == '\n':
                    event = UIEvent("key", key=KEY_ENTER)
                    self.manager.handle_event(event)
                elif key == '\t':
                    event = UIEvent("key", key=KEY_TAB)
                    self.manager.handle_event(event)
                elif key == '\b' or ord(key) == 127:
                    event = UIEvent("key", key=KEY_BACKSPACE)
                    self.manager.handle_event(event)
                else:
                    event = UIEvent("key", key=key)
                    self.manager.handle_event(event)
            elif isinstance(key, int):
                if key == curses.KEY_RESIZE:
                    self.renderer.refresh_dimensions()
                    h, w = self.screen.getmaxyx()
                    self.appwin.width = max(40, w - 6)
                    self.appwin.height = max(12, h - 6)
                    self.consolewin.width = max(34, w - 6)
                    self.consolewin.height = max(12, h - 6)
                    self.chatwin.width = max(34, w - 6)
                    self.chatwin.height = max(20, h - 6)
                    continue
                if key == curses.KEY_MOUSE:
                    try:
                        mouse_event_data = curses.getmouse()
                        event = self.parse_mouse(mouse_event_data)
                        if event:
                            self.manager.handle_event(event)
                    except curses.error:
                        continue
                elif key == -1:
                    time.sleep(0.01)
                    continue
                else:
                    event = UIEvent("key", key=key)
                    self.manager.handle_event(event)
                    if sys.platform == "darwin" and key > 127:
                        macos_option_map = {
                            ord('ƒ'): ord('f'), ord('∫'): ord('b'), ord('ç'): ord('c'), ord('∂'): ord('d'), ord('´'): ord('e'),
                            ord('©'): ord('g'), ord('˙'): ord('h'), ord('ˆ'): ord('i'), ord('∆'): ord('j'), ord('˚'): ord('k'),
                            ord('¬'): ord('l'), ord('µ'): ord('m'), ord('˜'): ord('n'), ord('ø'): ord('o'), ord('π'): ord('p'),
                            ord('œ'): ord('q'), ord('®'): ord('r'), ord('ß'): ord('s'), ord('†'): ord('t'), ord('¨'): ord('u'),
                            ord('√'): ord('v'), ord('∑'): ord('w'), ord('≈'): ord('x'), ord('¥'): ord('y'), ord('Ω'): ord('z'),
                        }
                        if key in macos_option_map:
                            event = UIEvent("key", key=("ALT", macos_option_map[key]))
                            if self.handle_alt(event):
                                continue

def main(stdscr):
    app = DemoApp(stdscr)
    try:
        app.mainloop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)