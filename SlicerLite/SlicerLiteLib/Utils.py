import os
import qt


class Utils:
    """Class used to store utils methods"""
    @staticmethod
    def getIconFilePath(icon):
        file_dir = os.path.dirname(__file__)
        return os.path.join(file_dir, "..", "Resources", "Icons", icon + ".png")

    @staticmethod
    def getIcon(iconName):
        return qt.QIcon(Utils.getIconFilePath(iconName))

    @staticmethod
    def getChildrenContainingName(widget, childString):
        if not hasattr(widget, "children"):
            return []
        else:
            return [child for child in widget.children() if childString.lower() in child.name.lower()]

    @staticmethod
    def getFirstChildContainingName(widget, childString):
        children = Utils.getChildrenContainingName(widget, childString)
        return children[0] if children else None