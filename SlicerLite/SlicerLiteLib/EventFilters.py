import qt


class DragAndDropEventFilter(qt.QWidget):
    def __init__(self, target, callback):
        super().__init__()
        self.target = target
        self.callback = callback

    def eventFilter(self, obj: qt.QObject, event: qt.QEvent):
        if obj == self.target and event.type() == qt.QEvent.Drop:
            event.accept()
            for url in event.mimeData().urls():
                if self.callback:
                    self.callback(url.path()[1:])
            return True
        return False
