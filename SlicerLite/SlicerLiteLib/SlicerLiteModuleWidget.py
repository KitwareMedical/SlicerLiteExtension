import qt, slicer

from .ButtonItemDelegate import DeleteButtonItemDelegate, DicomMetadataButtonItemDelegate
from .DataLoader import DataLoader
from .EventFilters import DragAndDropEventFilter
from .UIUtils import UIUtils
from .SlicerUtils import *
from .ItemModel import ItemModel, Item


class SlicerLiteModuleWidget(qt.QWidget):
    def __init__(self, parent=None):
        super(SlicerLiteModuleWidget, self).__init__(parent)
        qt.QVBoxLayout(self)
        self._lastOpenedDirectory = ""

        self.dataLoader = DataLoader()
        self.itemTableModel = ItemModel()
        self.itemTableView = qt.QTableView()
        self.deleteButtonItemDelegate = DeleteButtonItemDelegate()
        self.dicomTagsButtonItemDelegate = DicomMetadataButtonItemDelegate()

        self.buttonsDelegate = [self.deleteButtonItemDelegate, self.dicomTagsButtonItemDelegate]

        # Setup event filter
        self.filter = DragAndDropEventFilter(slicer.util.mainWindow(), self.loadDicomDirectory)
        slicer.util.mainWindow().installEventFilter(self.filter)

        self.setupUI()

    def setupUI(self):
        """
        Create and initialize UI components
        """
        self.setupTableViewLayout()
        self.setupRenderingLayout()
        self.setupSegmentationLayout()
        self.layout().addStretch()

    def setupTableViewLayout(self):
        """
        Setup the table view behavior/display
        """
        self.itemTableView.setItemDelegateForColumn(1, self.dicomTagsButtonItemDelegate)
        self.itemTableView.setItemDelegateForColumn(2, self.deleteButtonItemDelegate)
        # Hide headers
        self.itemTableView.horizontalHeader().hide()
        self.itemTableView.verticalHeader().hide()
        # Hide table borders
        self.itemTableView.setFrameStyle(qt.QFrame.NoFrame)
        self.itemTableView.horizontalHeader().setSectionResizeMode(qt.QHeaderView.Stretch)
        self.itemTableView.horizontalHeader().resizeSection(1, 32)
        self.itemTableView.horizontalHeader().resizeSection(2, 32)
        # Make lines no editabled
        self.itemTableView.setEditTriggers(qt.QAbstractItemView.NoEditTriggers)
        # Allow only one selection
        self.itemTableView.setSelectionMode(qt.QAbstractItemView.SingleSelection)

        self.itemTableView.clicked.connect(self.onTableViewItemClicked)
        self.itemTableView.setModel(self.itemTableModel)

        self.layout().addWidget(UIUtils.createButton("Load", callback=self.onClickLoadDicomDirectory))
        self.layout().addWidget(qt.QLabel("Loaded volumes:"))
        self.layout().addWidget(self.itemTableView)

    def setupRenderingLayout(self):
        """
        Get and place shift rendering sliders for volume rendering
        """
        self.renderingModule = slicer.util.getNewModuleGui(slicer.modules.volumerendering)
        self.shiftSliderWidget = slicer.util.findChild(self.renderingModule, "PresetOffsetSlider")
        self.shiftSliderWidget.setEnabled(False)

        layout = qt.QHBoxLayout()
        layout.addWidget(qt.QLabel("Rendering shift:"))
        layout.addWidget(self.shiftSliderWidget)

        self.layout().addLayout(layout)

    def setupSegmentationLayout(self):
        """
        Get and set the segmentation modules and simplify it
        """
        segmentEditorModule = slicer.modules.segmenteditor.widgetRepresentation()
        self.segmentEditorWidget = slicer.util.findChild(segmentEditorModule, "qMRMLSegmentEditorWidget")
        self.layout().addWidget(UIUtils.wrapInCollapsibleButton(segmentEditorModule, "Segmentation"))

        # Define list of hidden widgets inside segment editor widget
        hiddenWidgetsNames = ["SourceVolumeNodeLabel", "SourceVolumeNodeComboBox",
                                "SegmentationNodeLabel", "SegmentationNodeComboBox",
                                "SpecifyGeometryButton", "SwitchToSegmentationsButton"]
        addSegmentationButton = None
        for widget in self.segmentEditorWidget.children():
            if hasattr(widget, "objectName"):
                if widget.objectName in hiddenWidgetsNames:
                    widget.setVisible(False)
                if widget.objectName == "AddSegmentButton":
                    addSegmentationButton = widget

        # Need to add a new slot in order to avoid 3DSlicer to update this button visibility when adding a new segment
        if addSegmentationButton:
            addSegmentationButton.clicked.connect(self.segmentEditorWidget.rotateSliceViewsToSegmentation)

    def onClickLoadDicomDirectory(self):
        """
        User choose directory where DICOM will be extracted
        """
        # dirPath = qt.QFileDialog.getExistingDirectory(self,
        #                                              "Choose dicom file directory to load",
        #                                              self._lastOpenedDirectory)
        # if not dirPath:
        #     return
        # self.load_dicom_directory(dirPath)
        self.loadDicomDirectory(r"C:\Kitware\Dicom\DataAnonymized2")

    def loadDicomDirectory(self, directoryPath: str):
        """
        Add and load the input dicom dir into the DICOM database
        directory_path: Path to the directory that contains dicoms
        """
        qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)

        self._lastOpenedDirectory = directoryPath
        loadedVolumesNodes = self.dataLoader.loadDicomDirInDBAndExtractVolumesAsItems(self._lastOpenedDirectory)
        for volumeNode in loadedVolumesNodes:
            self.itemTableModel.addItem(Item(volumeNode))

        qt.QApplication.restoreOverrideCursor()

        # Don't show anything in slices
        SlicerUtils.showVolumeAsForegroundInSlices(None)
        SlicerUtils.showVolumeAsBackgroundInSlices(None)
        self.itemTableView.clearSelection()

    def setCurrentItem(self, item: Item):
        """
        Set the current item to the corresponding modules
        """
        self.renderingModule.setMRMLVolumeNode(item.volumeNode if item else None)
        self.shiftSliderWidget.setEnabled(bool(item.volumeNode) if item else False)
        self.segmentEditorWidget.setSegmentationNode(item.segmentationNode if item else None)
        self.segmentEditorWidget.setSourceVolumeNode(item.volumeNode if item else None)
        if item:
            self.segmentEditorWidget.rotateSliceViewsToSegmentation()

    def onTableViewItemClicked(self, modelIndex: qt.QModelIndex):
        """
        Update views and current item according to the clicked item
        """
        if not modelIndex.model():
            SlicerUtils.showVolumeAsForegroundInSlices(None)
            SlicerUtils.showVolumeAsBackgroundInSlices(None)
            self.itemTableView.clearSelection()
            self.setCurrentItem(None)
            return

        item = modelIndex.model().item(modelIndex.row()).data(ItemModel.ItemUserRole)
        # We only want to select line if user click on volume's name
        if modelIndex.column() != 0:
            return

        self.setCurrentItem(item)
        for button_delegate in self.buttonsDelegate:
            button_delegate.current_selected_row = modelIndex.row()
        modelIndex.model().toggleVolumeVisibility(modelIndex.row())

    def onDeleteItem(self):
        self.itemTableModel.viewport().update()

