import os

from typing import Callable
from ..component.modal import Modal
from ..component.window import Window
from ..component.multi_list import MultiList
from ..component.button import Button
from ..component.input import Input

class OpenDialog(Modal):
    def __init__(self, parent: Window, callback: Callable[[str], None]):
        super().__init__(50, 18, "Open File", parent)
        self.callback = callback
        self.path_input = Input(2, 2, self.width - 4, parent=self)
        self.path_input.value = os.getcwd()
        self.add(self.path_input)
        self.list = MultiList(2, 4, self.width - 4, self.height - 8, self.scan(self.path_input.value), parent=self)
        self.add(self.list)
        self.ok = Button(6, self.height - 3, 8, "OK", parent=self, window=self, onclick=self.on_ok)
        self.cancel = Button(16, self.height - 3, 10, "Cancel", parent=self, window=self, onclick=lambda: self.manager.remove(self))
        self.add(self.ok)
        self.add(self.cancel)

    def scan(self, p):
        try:
            items = os.listdir(p)
        except Exception:
            items = []
        dirs = [d + os.sep for d in items if os.path.isdir(os.path.join(p, d))]
        files = [f for f in items if os.path.isfile(os.path.join(p, f))]
        return sorted(dirs) + sorted(files)

    def on_ok(self):
        selection = [i for i, v in self.list.selectedItems.items() if v]
        if selection:
            name = self.list.items[selection[0]]
            path = os.path.join(self.path_input.value, name)
            if os.path.isdir(path):
                self.path_input.value = path
                self.list.items = self.scan(path)
                return
            else:
                self.callback(path)
                self.manager.remove(self)
                return
        path = self.path_input.value
        if os.path.exists(path) and os.path.isfile(path):
            self.callback(path)
            self.manager.remove(self)
        else:
            self.dispatchEvent("onerror", message="Invalid file")