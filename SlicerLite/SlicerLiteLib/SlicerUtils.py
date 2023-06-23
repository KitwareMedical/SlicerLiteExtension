import vtk, slicer


class SlicerUtils:
    """Class which stores utils functions relative to slicer"""

    SlicesNames = ["Red", "Yellow", "Green"]

    @staticmethod
    def createRenderingPreset():
        renderingPreset = slicer.modules.volumerendering.logic().GetPresetByName("CT-Cropped-Volume-Bone")
        scalarOpacityString = "10 -2048 0 -451 0 -450 0 1050 0.05 3661 0.1"
        piecewiseFunction = vtk.vtkPiecewiseFunction()
        renderingPreset.GetPiecewiseFunctionFromString(scalarOpacityString, piecewiseFunction)
        renderingPreset.SetScalarOpacity(piecewiseFunction)
        return renderingPreset

    @staticmethod
    def resetSliceViews():
        slicer.util.resetSliceViews()

    @staticmethod
    def resetOriginalSlicesOrientations():
        for sliceName in SlicerUtils.SlicesNames:
            orientation = slicer.app.layoutManager().sliceWidget(
                sliceName).sliceLogic().GetSliceNode().GetDefaultOrientation()
            slicer.app.layoutManager().sliceWidget(sliceName).setSliceOrientation(orientation)

    @staticmethod
    def showVolumeAsForegroundInSlices(volumeID):
        for color in SlicerUtils.SlicesNames:
            slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetForegroundVolumeID(
                volumeID)

    @staticmethod
    def showVolumeAsBackgroundInSlices(volumeID):
        for color in SlicerUtils.SlicesNames:
            slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(
                volumeID)

    @staticmethod
    def addNode(nodeType):
        return slicer.mrmlScene.AddNewNodeByClass(nodeType)
