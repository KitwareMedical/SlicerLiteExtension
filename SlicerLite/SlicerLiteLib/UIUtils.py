import qt
import ctk


def createButton(name, callback=None, isCheckable=False, icon=None) -> qt.QPushButton:
    """Helper function to create a button with a text, callback on click and checkable status

    Parameters
    ----------
    name: str
      Label of the button
    callback: Callable
      Called method when button is clicked
    isCheckable: bool
      If true, the button will be checkable
    icon: QImage
    """
    button = qt.QPushButton(name)
    if callback is not None:
        button.connect("clicked(bool)", callback)
    if icon:
        button.setIcon(icon)
    button.setCheckable(isCheckable)
    return button


def wrapInCollapsibleButton(childWidget, collapsibleText, isCollapsed=True):
    """Wraps input childWidget into a collapsible button.
    collapsibleText is writen next to collapsible button. Initial collapsed status is customizable
    (collapsed by default)

    :returns ctkCollapsibleButton
    """
    collapsibleButton = ctk.ctkCollapsibleButton()
    collapsibleButton.text = collapsibleText
    collapsibleButton.collapsed = isCollapsed
    collapsibleButtonLayout = qt.QVBoxLayout()
    collapsibleButtonLayout.addWidget(childWidget)
    collapsibleButton.setLayout(collapsibleButtonLayout)
    return collapsibleButton
