from ..component.window import Window

class Modal(Window):
    def __init__(self, width, height, title="Modal", parent=None):
        if parent:
            sw, sh = parent.width, parent.height
            sx, sy = parent.left, parent.top
            left = sx + max(0, (sw - width) // 2)
            top = sy + max(0, (sh - height) // 2)
        else:
            left = max(0, (80 - width) // 2)
            top = max(1, (24 - height) // 2)
        super().__init__(left, top, width, height, title, parent, modal=True)