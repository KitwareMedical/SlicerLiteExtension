import qt
import slicer

from dataclasses import dataclass

from SlicerLiteLib import SlicerUtils


@dataclass
class VolumeHierarchy:
    """ Hold  """
    patientUID: str
    studyUID: str
    seriesUID: str
    volumeNodeID: str
    seriesDescription: str


class VolumeItem:
    def __init__(self, volumeHierarchy: VolumeHierarchy, numberOfSlices, volumeNode=None):
        self.volumeHierarchy = volumeHierarchy
        self.numberOfSlices = numberOfSlices
        self.volumeNode = volumeNode if volumeNode else slicer.util.getNode(volumeHierarchy.volumeNodeID)
        self.volumeName = self.volumeNode.GetName()
        self.volumeRenderingDisplayNode = self.initializeRendering()
        self.volumeNode.SetDisplayVisibility(False)
        self.segmentationNode = SlicerUtils.addNode("vtkMRMLSegmentationNode")
        self.segmentationNode.SetName("Segmentation_" + self.volumeName)
        self.shiftRenderingValue = (self.getMinScalarValue() + self.getMaxScalarValue()) / 2

    def __ne__(self, other):
        return self.volumeName == other.volumeName

    def __del__(self):
        slicer.mrmlScene.RemoveNode(self.volumeNode)
        slicer.mrmlScene.RemoveNode(self.segmentationNode)

    def getMinScalarValue(self):
        """
        Return the minimum scalar value of the volume node
        """
        return self.volumeNode.GetImageData().GetPointData().GetScalars().GetRange()[0]

    def getMaxScalarValue(self):
        """
        Return the maximum scalar value of the volume node
        """
        return self.volumeNode.GetImageData().GetPointData().GetScalars().GetRange()[1]

    def isDicomVolumeItem(self):
        return self.volumeHierarchy.volumeNodeID != ""

    def initializeRendering(self):
        volRenLogic = slicer.modules.volumerendering.logic()
        displayNode = volRenLogic.CreateDefaultVolumeRenderingNodes(self.volumeNode)
        displayNode.SetVisibility(False)
        renderingPreset = SlicerUtils.createRenderingPreset()
        displayNode.GetVolumePropertyNode().Copy(renderingPreset)
        return displayNode

    def getVisibility(self) -> bool:
        return self.volumeNode.GetDisplayNode().GetVisibility()

    def setVisibility(self, visible):
        self.volumeNode.SetDisplayVisibility(visible)
        self.segmentationNode.SetDisplayVisibility(visible)
        if visible:
            SlicerUtils.showVolumeAsForegroundInSlices(self.volumeNode.GetID())
            SlicerUtils.resetSliceViews()
            SlicerUtils.resetOriginalSlicesOrientations()
            slicer.util.resetThreeDViews()

    def toggleVisibility(self):
        self.setVisibility(not self.getVisibility())


class VolumeItemModel(qt.QStandardItemModel):
    ItemUserRole = qt.Qt.UserRole + 1

    def __init__(self, parent=None):
        super(VolumeItemModel, self).__init__(parent)

    def addItem(self, item: VolumeItem):
        def createItem(i):
            displayText = item.volumeName + "(" + str(item.numberOfSlices) + ")" if i == 0 else ""
            newItem = qt.QStandardItem(displayText)
            newItem.setData(item, VolumeItemModel.ItemUserRole)
            return newItem

        self.appendRow([createItem(i) for i in range(3)])
        return self.index(self.rowCount(), self.columnCount())

    def getVolumeItemFromId(self, volumeId):
        """
        Get the VolumeItem at the id row position.
        If not found, then return None
        """
        if volumeId < self.rowCount():
            return self.item(volumeId).data(VolumeItemModel.ItemUserRole)
        return None

    def getVolumeIdFromVolumeItem(self, volumeItem: VolumeItem):
        """
        Get the index of the input volumeItem in the model list
        If not found, return -1
        """
        for i in range(self.rowCount()):
            if self.getVolumeItemFromId(i) == volumeItem:
                return i
        return -1

    def toggleVolumeVisibility(self, itemId):
        self.item(itemId).data(VolumeItemModel.ItemUserRole).toggleVisibility()
        currentItemVisibility = self.item(itemId).data(VolumeItemModel.ItemUserRole).getVisibility()
        if currentItemVisibility:
            # Hide all other volumes to keep one visible volume
            for rowID in range(self.rowCount()):
                if rowID == itemId:
                    continue
                self.item(rowID).data(VolumeItemModel.ItemUserRole).setVisibility(False)
        # Allow to notify the view that model as changed, so that the view can repaint itself
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))
