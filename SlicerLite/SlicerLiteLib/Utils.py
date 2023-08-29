import os
import qt


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