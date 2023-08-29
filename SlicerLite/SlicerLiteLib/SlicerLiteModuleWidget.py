import qt, slicer

from .ButtonItemDelegate import DeleteButtonItemDelegate, DicomMetadataButtonItemDelegate
from .DataLoader import DataLoader
from .EventFilters import DragAndDropEventFilter
from .UIUtils import *
from .Settings import SlicerLiteSettings
from .SlicerUtils import *
from .VolumeItemModel import VolumeItemModel, VolumeItem




class SlicerLiteModuleWidget(qt.QWidget):
    def __init__(self, parent=None):
        super(SlicerLiteModuleWidget, self).__init__(parent)
        qt.QVBoxLayout(self)
        self.settings = qt.QSettings()
        self._lastOpenedDirectory = ""

        self.dataLoader = DataLoader()
        self.itemTableModel = VolumeItemModel()
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

        self.layout().addWidget(createButton("Load", callback=self.onClickLoadDicomDirectory))
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
        self.segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
        self.layout().addWidget(wrapInCollapsibleButton(self.segmentEditorWidget, "Segmentation"))

        # Define list of hidden widgets inside segment editor widget
        hiddenWidgetsNames = ["SourceVolumeNodeLabel", "SourceVolumeNodeComboBox",
                                "SegmentationNodeLabel", "SegmentationNodeComboBox",
                                "SpecifyGeometryButton", "SwitchToSegmentationsButton"]
        for hiddenWidgetName in hiddenWidgetsNames:
            widget = slicer.util.findChild(self.segmentEditorWidget, hiddenWidgetName)
            if widget:
                widget.setVisible(False)

        segmentButtonWidget = slicer.util.findChild(self.segmentEditorWidget, "AddSegmentButton")
        if segmentButtonWidget:
            # Need to add a new slot in order to avoid 3DSlicer to update this button visibility when adding a new segment
            segmentButtonWidget.clicked.connect(self.segmentEditorWidget.rotateSliceViewsToSegmentation)

    def onClickLoadDicomDirectory(self):
        """
        User choose directory where DICOM will be extracted
        """
        dirPath = qt.QFileDialog.getExistingDirectory(self,
                                                     "Choose dicom file directory to load",
                                                     SlicerLiteSettings.LastOpenedDirectory)
        if not dirPath:
            return
        self.loadDicomDirectory(dirPath)

    def loadDicomDirectory(self, directoryPath: str):
        """
        Add and load the input dicom dir into the DICOM database
        directory_path: Path to the directory that contains dicoms
        """
        qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)

        SlicerLiteSettings.LastOpenedDirectory = directoryPath
        loadedVolumesNodes = self.dataLoader.loadDicomDirInDBAndExtractVolumesAsItems(SlicerLiteSettings.LastOpenedDirectory)

        qt.QApplication.restoreOverrideCursor()

        if len(loadedVolumesNodes) == 0:
            return

        lastAddedItem = None
        for volumeNode in loadedVolumesNodes:
            lastAddedItem = VolumeItem(volumeNode)
            self.itemTableModel.addItem(lastAddedItem)


        self.setCurrentItem(lastAddedItem)
        self.itemTableView.clearSelection()

    def setCurrentItem(self, item: VolumeItem):
        """
        Set the current item to the corresponding modules
        """
        self.renderingModule.setMRMLVolumeNode(item.volumeNode if item else None)
        self.shiftSliderWidget.setEnabled(bool(item.volumeNode) if item else False)
        self.segmentEditorWidget.setSegmentationNode(item.segmentationNode if item else None)
        self.segmentEditorWidget.setSourceVolumeNode(item.volumeNode if item else None)
        showVolumeAsForegroundInSlices(item.volumeNode.GetID() if item else None)
        showVolumeAsBackgroundInSlices(item.volumeNode.GetID() if item else None)
        # self.itemTableView.setCurrentIndex(self.itemTableModel.indexFromItem(item))
        if item:
            self.segmentEditorWidget.rotateSliceViewsToSegmentation()

    def onTableViewItemClicked(self, modelIndex: qt.QModelIndex):
        """
        Update views and current item according to the clicked item
        """
        if not modelIndex.model():
            self.itemTableView.clearSelection()
            self.setCurrentItem(None)
            return

        item = modelIndex.model().item(modelIndex.row()).data(VolumeItemModel.ItemUserRole)
        # We only want to select line if user click on volume's name
        if modelIndex.column() != 0:
            return

        self.setCurrentItem(item)
        for button_delegate in self.buttonsDelegate:
            button_delegate.current_selected_row = modelIndex.row()
        modelIndex.model().toggleVolumeVisibility(modelIndex.row())

