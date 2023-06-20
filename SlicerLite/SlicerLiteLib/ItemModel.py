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
        self.volumeRenderingDisplayNode = self.initialize_rendering()
        self.volumeNode.SetDisplayVisibility(False)
        self.segmentationNode = SlicerUtils.addNode("vtkMRMLSegmentationNode")
        self.segmentationNode.SetName("Segmentation_" + self.volumeName)

    def __del__(self):
        slicer.mrmlScene.RemoveNode(self.volumeNode)
        slicer.mrmlScene.RemoveNode(self.segmentationNode)

    def initialize_rendering(self):
        volRenLogic = slicer.modules.volumerendering.logic()
        displayNode = volRenLogic.CreateDefaultVolumeRenderingNodes(self.volumeNode)
        displayNode.SetVisibility(False)
        renderingPreset = SlicerUtils.create_rendering_preset()
        displayNode.GetVolumePropertyNode().Copy(renderingPreset)
        return displayNode

    def get_visibility(self) -> bool:
        return self.volumeNode.GetDisplayNode().GetVisibility()

    def set_visibility(self, visible):
        self.volumeNode.SetDisplayVisibility(visible)
        if visible:
            SlicerUtils.show_volume_as_foreground_in_slices(self.volumeNode.GetID())
            SlicerUtils.reset_slice_views()
            SlicerUtils.reset_original_slices_orientations()
            slicer.util.resetThreeDViews()

    def toggle_visibility(self) -> None:
        self.set_visibility(not self.get_visibility())


class ItemModel(qt.QStandardItemModel):
    ItemUserRole = qt.Qt.UserRole + 1

    def __init__(self, parent=None):
        super(ItemModel, self).__init__(parent)

    def add_item(self, item: Item):
        def create_item():
            new_item = qt.QStandardItem(item.volumeName)
            new_item.setData(item, ItemModel.ItemUserRole)
            return new_item

        self.appendRow([create_item() for _ in range(3)])

    def toggle_volume_visibility(self, itemId):
        self.item(itemId).data(ItemModel.ItemUserRole).toggle_visibility()
        currentItemVisibility = self.item(itemId).data(ItemModel.ItemUserRole).get_visibility()
        if currentItemVisibility:
            # Hide all other volumes to keep one visible volume
            for rowID in range(self.rowCount()):
                if rowID == itemId:
                    continue
                self.item(rowID).data(ItemModel.ItemUserRole).set_visibility(False)
        # Allow to notify the view that model as changed, so that the view can repaint itself
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))