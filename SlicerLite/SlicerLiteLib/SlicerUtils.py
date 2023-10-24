import vtk
import slicer

SlicesNames = ["Red", "Yellow", "Green"]


def createRenderingPreset():
    renderingPreset = slicer.modules.volumerendering.logic().GetPresetByName("CT-Cropped-Volume-Bone")
    scalarOpacityString = "10 -2048 0 -451 0 -450 0 1050 0.05 3661 0.1"
    piecewiseFunction = vtk.vtkPiecewiseFunction()
    renderingPreset.GetPiecewiseFunctionFromString(scalarOpacityString, piecewiseFunction)
    renderingPreset.SetScalarOpacity(piecewiseFunction)
    return renderingPreset


def resetSliceViews():
    slicer.util.resetSliceViews()


def resetOriginalSlicesOrientations():
    for sliceName in SlicesNames:
        orientation = slicer.app.layoutManager().sliceWidget(
            sliceName).sliceLogic().GetSliceNode().GetDefaultOrientation()
        slicer.app.layoutManager().sliceWidget(sliceName).setSliceOrientation(orientation)


def showVolumeAsForegroundInSlices(volumeID):
    for color in SlicesNames:
        slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetForegroundVolumeID(
            volumeID)


def showVolumeAsBackgroundInSlices(volumeID):
    for color in SlicesNames:
        slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(
            volumeID)


def addNode(nodeType):
    return slicer.mrmlScene.AddNewNodeByClass(nodeType)


def getDicomWidget():
    try:
        return slicer.modules.DICOMWidget
    except AttributeError:
        return slicer.modules.dicom.widgetRepresentation().self()


def updateMenuBarsAndToolBarsSlicerVisibility(visible):
    mainWindow = slicer.util.mainWindow()
    mainWindow.menuBar().setVisible(visible)
    mainWindow.MainToolBar.setVisible(visible)
    mainWindow.ModuleSelectorToolBar.setVisible(visible)
    slicer.util.setToolbarsVisible(visible)


def getToolBarVisibilityButton():
    """
    Create and return a QPushButton checkable which show/hide slicer's (tool/menu)bar
    """
    from SlicerLiteLib import UIUtils, Utils

    buttonVisibility = None

    def onVisibilityToolbarButtonClicked(isChecked):
        updateMenuBarsAndToolBarsSlicerVisibility(isChecked)
        if isChecked:
            buttonVisibility.setIcon(Utils.getIcon("hide_toolbar"))
        else:
            buttonVisibility.setIcon(Utils.getIcon("toolbar"))

    buttonVisibility = UIUtils.createButton("", isCheckable=True, callback=onVisibilityToolbarButtonClicked,
                                            icon=Utils.getIcon("toolbar"))
    # Add new connection to handle when setChecked is called to correctly update icon
    buttonVisibility.connect("toggled(bool)", onVisibilityToolbarButtonClicked)
    return buttonVisibility
