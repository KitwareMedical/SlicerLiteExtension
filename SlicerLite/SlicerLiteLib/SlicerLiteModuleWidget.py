import qt, slicer

from SlicerLiteLib import Delegates, DicomDataLoader, EventFilters, UIUtils, Settings, SlicerUtils, Model




class SlicerLiteModuleWidget(qt.QWidget):
    def __init__(self, parent=None):
        super(SlicerLiteModuleWidget, self).__init__(parent)
        qt.QVBoxLayout(self)
        self.settings = qt.QSettings()
        self.lastSelectedRowIndex = -1

        self.dicomDataLoader = DicomDataLoader()
        self.itemTableModel = Model.VolumeItemModel()
        self.itemTableView = qt.QTableView()
        self.deleteButtonItemDelegate = Delegates.DeleteButtonItemDelegate()
        self.dicomTagsButtonItemDelegate = Delegates.DicomMetadataButtonItemDelegate()
        self.deleteButtonItemDelegate.modelDeletedSignal.connect(self.onDeleteVolumeItem)

        self.buttonsDelegate = [self.deleteButtonItemDelegate, self.dicomTagsButtonItemDelegate]

        # Setup event filter
        self.filter = EventFilters.DragAndDropEventFilter(slicer.util.mainWindow(), self.loadDicomDirectory)
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
        self.itemTableView.resizeColumnsToContents()
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
        self.segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
        self.segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
        self.segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
        self.segmentEditorWidget.setMRMLSegmentEditorNode(self.segmentEditorNode)

        self.layout().addWidget(UIUtils.wrapInCollapsibleButton(self.segmentEditorWidget, "Segmentation"))

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
            segmentButtonWidget.clicked.connect(self.rotateSliceViewsToSegmentation)

    def rotateSliceViewsToSegmentation(self):
        self.segmentEditorWidget.rotateSliceViewsToSegmentation()

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

        Settings.SlicerLiteSettings.LastOpenedDirectory = directoryPath
        loadedVolumesNodes = self.dicomDataLoader.loadDicomDirInDBAndExtractVolumesAsItems(Settings.SlicerLiteSettings.LastOpenedDirectory)

        qt.QApplication.restoreOverrideCursor()

        if len(loadedVolumesNodes) == 0:
            return

        lastAddedItem = None
        for volumeNode in loadedVolumesNodes:
            lastAddedItem = Model.VolumeItem(volumeNode)
            index = self.itemTableModel.addItem(lastAddedItem)
            self.itemTableView.closePersistentEditor(index)

        if lastAddedItem:
            self.setCurrentVolumeItem(lastAddedItem)
            self.itemTableView.clearSelection()

    def setCurrentVolumeItem(self, volumeItem: Model.VolumeItem):
        """
        Set the current item to the corresponding modules and toggle its visibility
        """
        self.renderingModule.setMRMLVolumeNode(volumeItem.volumeNode if volumeItem else None)
        self.shiftSliderWidget.setEnabled(bool(volumeItem.volumeNode) if volumeItem else False)
        self.segmentEditorWidget.setSegmentationNode(volumeItem.segmentationNode if volumeItem else None)
        self.segmentEditorWidget.setSourceVolumeNode(volumeItem.volumeNode if volumeItem else None)
        SlicerUtils.showVolumeAsForegroundInSlices(volumeItem.volumeNode.GetID() if volumeItem else None)
        SlicerUtils.showVolumeAsBackgroundInSlices(volumeItem.volumeNode.GetID() if volumeItem else None)
        # self.itemTableView.setCurrentIndex(self.itemTableModel.indexFromItem(item))
        currentVolumeItemId = self.itemTableModel.getVolumeIdFromVolumeItem(volumeItem)
        self.changeSelectedRow(currentVolumeItemId)
        # Turn 3D visibility of volume to TRUE
        self.itemTableModel.toggleVolumeVisibility(currentVolumeItemId)
        if volumeItem:
            self.rotateSliceViewsToSegmentation()

    def changeSelectedRow(self, selectedRowId):
        """
        Manually change the selected row to the selectedRowId
        """
        if 0 <= selectedRowId < self.itemTableModel.rowCount:
            self.itemTableView.clearSelection()
            self.itemTableView.selectionModel().setCurrentIndex(self.itemTableModel.index(selectedRowId, 0), qt.QItemSelectionModel.Select)

    def onDeleteVolumeItem(self):
        """
        Called after an item is deleted
        Set the current item to the first one
        """
        if self.itemTableModel.rowCount() > 0:
            self.setCurrentVolumeItem(self.itemTableModel.getVolumeItemFromId(0))
            self.setCurrentSelectedLineOnTableView(0)
            self.lastSelectedRowIndex = 0

    def setCurrentSelectedLineOnTableView(self, rowID):
        """
        Update the display columns item on the input rowID (open and close persistent editors = buttons)
        """
        if self.lastSelectedRowIndex >= 0:
            self.itemTableView.closePersistentEditor(self.itemTableModel.index(self.lastSelectedRowIndex, 1))
            self.itemTableView.closePersistentEditor(self.itemTableModel.index(self.lastSelectedRowIndex, 2))
        self.itemTableView.openPersistentEditor(self.itemTableModel.index(rowID, 1))
        self.itemTableView.openPersistentEditor(self.itemTableModel.index(rowID, 2))
        self.lastSelectedRowIndex = rowID

    def onTableViewItemClicked(self, modelIndex: qt.QModelIndex):
        """
        Update views and current item according to the clicked item
        """
        if not modelIndex.model():
            self.itemTableView.clearSelection()
            self.setCurrentVolumeItem(None)
            return

        volumeItem = modelIndex.model().item(modelIndex.row()).data(Model.VolumeItemModel.ItemUserRole)
        # We only want to select line if user click on volume's name
        if modelIndex.column() != 0 or modelIndex.row() == self.lastSelectedRowIndex:
            return

        # Save current shift rendering value
        if self.lastSelectedRowIndex >= 0:
            item = self.itemTableModel.getVolumeItemFromId(self.lastSelectedRowIndex)
            item.shiftRenderingValue = self.shiftSliderWidget.value

        self.setCurrentVolumeItem(volumeItem)
        self.setCurrentSelectedLineOnTableView(modelIndex.row())

        # Set current shift rendering value
        if self.lastSelectedRowIndex >= 0:
            newItem = self.itemTableModel.getVolumeItemFromId(self.lastSelectedRowIndex)
            self.shiftSliderWidget.blockSignals(True)
            self.shiftSliderWidget.setValue(newItem.shiftRenderingValue)
            self.shiftSliderWidget.blockSignals(False)
