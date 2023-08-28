import logging
import slicer
from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleLogic,
    ScriptedLoadableModuleWidget,
    ScriptedLoadableModuleTest,
)
from slicer.util import VTKObservationMixin

from SlicerLiteLib import SlicerLiteModuleWidget


#
# SlicerLite
#

class SlicerLite(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "SlicerLite"
        self.parent.categories = ["Examples"]
        self.parent.dependencies = []
        self.parent.contributors = ["Laurenn Lam (Kitware SAS), Thibault Pelletier (Kitware SAS), Julien Finet (Kitware SAS)"]
        self.parent.helpText = """
                               Slicer extension with a simple UI to load/visualize/segment your dicom data
                               """
        self.parent.acknowledgementText = """
                                          This extension was originally developed by Laurenn Lam, Thibault Pelletier, Julien Finet, Kitware SAS.
                                          """


#
# SlicerLiteWidget
#

class SlicerLiteWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.setup(self)

        self.ui = SlicerLiteModuleWidget()
        self.layout.addWidget(self.ui)
