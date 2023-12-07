import qt


class DragAndDropEventFilter(qt.QWidget):
    def __init__(self, target, callback, parent=None):
        super(DragAndDropEventFilter, self).__init__(parent)
        self.target = target
        self.callback = callback

    def eventFilter(self, obj: qt.QObject, event: qt.QEvent):
        if not self.callback or obj != self.target or event.type() != qt.QEvent.Drop:
            return False

        event.accept()
        for url in event.mimeData().urls():
            if self.callback:
                self.callback(url.path()[1:])
        return True
