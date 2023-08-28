import qt
import slicer

from dataclasses import dataclass

from .SlicerUtils import *


@dataclass
class VolumeHierarchy:
    """ Hold  """
    patientUID: str
    studyUID: str
    seriesUID: str
    volumeNodeID: str
    seriesDescription: str


class VolumeItem:
    def __init__(self, volumeHierarchy: VolumeHierarchy):
        self.volumeHierarchy = volumeHierarchy
        self.volumeNode = slicer.util.getNode(volumeHierarchy.volumeNodeID)
        self.volumeName = self.volumeNode.GetName()
        self.volumeRenderingDisplayNode = self.initializeRendering()
        self.volumeNode.SetDisplayVisibility(False)
        self.segmentationNode = addNode("vtkMRMLSegmentationNode")
        self.segmentationNode.SetName("Segmentation_" + self.volumeName)

    def __del__(self):
        slicer.mrmlScene.RemoveNode(self.volumeNode)
        slicer.mrmlScene.RemoveNode(self.segmentationNode)

    def initializeRendering(self):
        volRenLogic = slicer.modules.volumerendering.logic()
        displayNode = volRenLogic.CreateDefaultVolumeRenderingNodes(self.volumeNode)
        displayNode.SetVisibility(False)
        renderingPreset = createRenderingPreset()
        displayNode.GetVolumePropertyNode().Copy(renderingPreset)
        return displayNode

    def getVisibility(self) -> bool:
        return self.volumeNode.GetDisplayNode().GetVisibility()

    def set_visibility(self, visible):
        self.volumeNode.SetDisplayVisibility(visible)
        if visible:
            showVolumeAsForegroundInSlices(self.volumeNode.GetID())
            resetSliceViews()
            resetOriginalSlicesOrientations()
            slicer.util.resetThreeDViews()

    def toggle_visibility(self):
        self.set_visibility(not self.getVisibility())


class VolumeItemModel(qt.QStandardItemModel):
    ItemUserRole = qt.Qt.UserRole + 1

    def __init__(self, parent=None):
        super(VolumeItemModel, self).__init__(parent)

    def addItem(self, item: VolumeItem):
        def createItem():
            newItem = qt.QStandardItem(item.volumeName)
            newItem.setData(item, VolumeItemModel.ItemUserRole)
            return newItem

        self.appendRow([createItem() for _ in range(3)])

    def toggleVolumeVisibility(self, itemId):
        self.item(itemId).data(VolumeItemModel.ItemUserRole).toggle_visibility()
        currentItemVisibility = self.item(itemId).data(VolumeItemModel.ItemUserRole).getVisibility()
        if currentItemVisibility:
            # Hide all other volumes to keep one visible volume
            for rowID in range(self.rowCount()):
                if rowID == itemId:
                    continue
                self.item(rowID).data(VolumeItemModel.ItemUserRole).set_visibility(False)
        # Allow to notify the view that model as changed, so that the view can repaint itself
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))