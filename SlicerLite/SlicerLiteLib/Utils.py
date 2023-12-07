import os
import qt

from itertools import count


def getIconFilePath(icon):
    file_dir = os.path.dirname(__file__)
    return os.path.join(file_dir, "..", "Resources", "Icons", icon + ".png")


def getIcon(iconName):
    return qt.QIcon(getIconFilePath(iconName))


def getChildrenContainingName(widget, childString):
    if not hasattr(widget, "children"):
        return []
    else:
        return [child for child in widget.children() if childString.lower() in child.name.lower()]


def getFirstChildContainingName(widget, childString):
    children = getChildrenContainingName(widget, childString)
    return children[0] if children else None


class Signal(object):
    """ Qt like signal slot connections. Enables using the same semantics with Slicer as qt.Signal lead to application
    crash.
    (see : https://discourse.slicer.org/t/custom-signal-slots-with-pythonqt/3278/5)
    """

    def __init__(self, *typeInfo):
        self._id = count(0, 1)
        self._connectDict = {}
        self._typeInfo = str(typeInfo)

    def emit(self, *args, **kwargs):
        for slot in self._connectDict.values():
            slot(*args, **kwargs)

    def connect(self, slot):
        nextId = next(self._id)
        self._connectDict[nextId] = slot
        return nextId

    def disconnect(self, connectId):
        if connectId in self._connectDict:
            del self._connectDict[connectId]
            return True
        return False
