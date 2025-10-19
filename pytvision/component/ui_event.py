class UIEvent:
    def __init__(self, type_, **kw):
        self.type = type_
        self.data = kw