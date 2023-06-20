import vtk, slicer


class SlicerUtils:
    """Class which stores utils functions relative to slicer"""

    SlicesNames = ["Red", "Yellow", "Green"]

    @staticmethod
    def create_rendering_preset():
        renderingPreset = slicer.modules.volumerendering.logic().GetPresetByName("CT-Cropped-Volume-Bone")
        scalarOpacityString = "10 -2048 0 -451 0 -450 0 1050 0.05 3661 0.1"
        piecewiseFunction = vtk.vtkPiecewiseFunction()
        renderingPreset.GetPiecewiseFunctionFromString(scalarOpacityString, piecewiseFunction)
        renderingPreset.SetScalarOpacity(piecewiseFunction)
        return renderingPreset

    @staticmethod
    def reset_slice_views():
        slicer.util.resetSliceViews()

    @staticmethod
    def reset_original_slices_orientations():
        for sliceName in SlicerUtils.SlicesNames:
            orientation = slicer.app.layoutManager().sliceWidget(
                sliceName).sliceLogic().GetSliceNode().GetDefaultOrientation()
            slicer.app.layoutManager().sliceWidget(sliceName).setSliceOrientation(orientation)

    @staticmethod
    def show_volume_as_foreground_in_slices(volumeID):
        for color in SlicerUtils.SlicesNames:
            slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetForegroundVolumeID(
                volumeID)

    @staticmethod
    def show_volume_as_background_in_slices(volumeID):
        for color in SlicerUtils.SlicesNames:
            slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(
                volumeID)

    @staticmethod
    def addNode(nodeType):
        return slicer.mrmlScene.AddNewNodeByClass(nodeType)
