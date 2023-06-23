import qt
import slicer

from .SlicerUtils import *


class DICOMItem:
    def __init__(self, patientUID, studyUID, seriesUID, volumeNodeID):
        self.patientUID = patientUID
        self.studyUID = studyUID
        self.seriesUID = seriesUID
        self.volumeNodeID = volumeNodeID


class Item:
    def __init__(self, dicomItem: DICOMItem):
        self.dicomItem = dicomItem
        self.volumeNode = slicer.util.getNode(dicomItem.volumeNodeID)
        self.volumeName = self.volumeNode.GetName()
        self.volumeRenderingDisplayNode = self.initializeRendering()
        self.volumeNode.SetDisplayVisibility(False)
        self.segmentationNode = SlicerUtils.addNode("vtkMRMLSegmentationNode")
        self.segmentationNode.SetName("Segmentation_" + self.volumeName)

    def __del__(self):
        slicer.mrmlScene.RemoveNode(self.volumeNode)
        slicer.mrmlScene.RemoveNode(self.segmentationNode)

    def initializeRendering(self):
        volRenLogic = slicer.modules.volumerendering.logic()
        displayNode = volRenLogic.CreateDefaultVolumeRenderingNodes(self.volumeNode)
        displayNode.SetVisibility(False)
        renderingPreset = SlicerUtils.createRenderingPreset()
        displayNode.GetVolumePropertyNode().Copy(renderingPreset)
        return displayNode

    def getVisibility(self) -> bool:
        return self.volumeNode.GetDisplayNode().GetVisibility()

    def set_visibility(self, visible):
        self.volumeNode.SetDisplayVisibility(visible)
        if visible:
            SlicerUtils.showVolumeAsForegroundInSlices(self.volumeNode.GetID())
            SlicerUtils.resetSliceViews()
            SlicerUtils.resetOriginalSlicesOrientations()
            slicer.util.resetThreeDViews()

    def toggle_visibility(self):
        self.set_visibility(not self.getVisibility())


class ItemModel(qt.QStandardItemModel):
    ItemUserRole = qt.Qt.UserRole + 1

    def __init__(self, parent=None):
        super(ItemModel, self).__init__(parent)

    def addItem(self, item: Item):
        def createItem():
            newItem = qt.QStandardItem(item.volumeName)
            newItem.setData(item, ItemModel.ItemUserRole)
            return newItem

        self.appendRow([createItem() for _ in range(3)])

    def toggleVolumeVisibility(self, itemId):
        self.item(itemId).data(ItemModel.ItemUserRole).toggle_visibility()
        currentItemVisibility = self.item(itemId).data(ItemModel.ItemUserRole).getVisibility()
        if currentItemVisibility:
            # Hide all other volumes to keep one visible volume
            for rowID in range(self.rowCount()):
                if rowID == itemId:
                    continue
                self.item(rowID).data(ItemModel.ItemUserRole).set_visibility(False)
        # Allow to notify the view that model as changed, so that the view can repaint itself
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))