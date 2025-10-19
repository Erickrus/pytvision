import os

from typing import Callable
from ..component.modal import Modal
from ..component.window import Window
from ..component.multi_list import MultiList
from ..component.button import Button
from ..component.input import Input

class SaveDialog(Modal):
    def __init__(self, parent: Window, suggested="out.txt", callback: Callable[[str], None] = None):
        super().__init__(50, 10, "Save File", parent)
        self.callback = callback
        self.input = Input(2, 2, self.width - 4, parent=self)
        self.input.value = os.path.join(os.getcwd(), suggested)
        self.add(self.input)
        self.ok = Button(6, self.height - 3, 8, "Save", parent=self, window=self, onclick=self.on_save)
        self.cancel = Button(16, self.height - 3, 10, "Cancel", parent=self, window=self, onclick=lambda: self.manager.remove(self))
        self.add(self.ok)
        self.add(self.cancel)

    def on_save(self):
        p = self.input.value
        try:
            open(p, "w").write("")
            if self.callback:
                self.callback(p)
            self.manager.remove(self)
        except Exception as e:
            self.dispatchEvent("onerror", message=str(e))