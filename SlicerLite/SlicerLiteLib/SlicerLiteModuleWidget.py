import qt, slicer

from SlicerLiteLib import Delegates, DataLoader, EventFilters, UIUtils, Settings, SlicerUtils, Model, SlicerLiteSettings




class SlicerLiteModuleWidget(qt.QWidget):
    def __init__(self, parent=None):
        super(SlicerLiteModuleWidget, self).__init__(parent)
        qt.QVBoxLayout(self)
        self.settings = qt.QSettings()
        self.lastSelectedRowIndex = -1

        self.dataLoader = DataLoader()
        self.itemTableModel = Model.VolumeItemModel()
        self.itemTableView = qt.QTableView()
        self.deleteButtonItemDelegate = Delegates.DeleteButtonItemDelegate()
        self.dicomTagsButtonItemDelegate = Delegates.DicomMetadataButtonItemDelegate()
        self.deleteButtonItemDelegate.modelDeletedSignal.connect(self.onDeleteVolumeItem)
        self.deleteButtonItemDelegate.modelDeletedSignal.connect(self.dataLoader.volumeDeleted)

        # Setup event filter
        self.filter = EventFilters.DragAndDropEventFilter(slicer.util.mainWindow(), self.loadInputData)
        slicer.util.mainWindow().installEventFilter(self.filter)

        self.setupUI()

    def showEvent(self, event: qt.QShowEvent):
        SlicerUtils.updateMenubarsAndToolBarsSlicerVisibility(False)

    def hideEvent(self, event: qt.QHideEvent):
        SlicerUtils.updateMenubarsAndToolBarsSlicerVisibility(True)

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
        Set up the table view behavior/display
        """
        self.itemTableView.setItemDelegateForColumn(1, self.dicomTagsButtonItemDelegate)
        self.itemTableView.setItemDelegateForColumn(2, self.deleteButtonItemDelegate)
        # Hide headers
        self.itemTableView.horizontalHeader().hide()
        self.itemTableView.verticalHeader().hide()
        # Hide contours table borders
        self.itemTableView.setFrameStyle(qt.QFrame.NoFrame)
        # Hide grid borders
        self.itemTableView.showGrid = False
        # self.itemTableView.horizontalHeader().setSectionResizeMode(qt.QHeaderView.Stretch)
        # self.itemTableView.horizontalHeader().resizeSection(1, 32)
        # self.itemTableView.horizontalHeader().resizeSection(2, 32)
        # self.itemTableView.setColumnWidth(0, 80)
        # self.itemTableView.setColumnWidth(1, 22)
        # self.itemTableView.setColumnWidth(2, 22)
        self.itemTableView.resizeColumnsToContents()
        # Make lines no editable
        self.itemTableView.setEditTriggers(qt.QAbstractItemView.NoEditTriggers)
        # Allow only one selection
        self.itemTableView.setSelectionMode(qt.QAbstractItemView.SingleSelection)

        self.itemTableView.clicked.connect(self.onTableViewItemClicked)
        self.itemTableView.setModel(self.itemTableModel)

        layoutLoadVolumes = qt.QHBoxLayout()
        layoutLoadVolumes.addWidget(UIUtils.createButton("Load DICOM", callback=self.onClickLoadDicomVolume))
        layoutLoadVolumes.addWidget(UIUtils.createButton("Load volume", callback=self.onClickLoadVolume))

        self.layout().addLayout(layoutLoadVolumes)
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

    def onClickLoadDicomVolume(self):
        """
        User choose directory where DICOM will be extracted
        """
        dirPath = qt.QFileDialog.getExistingDirectory(self,
                                                      "Choose dicom file directory to load",
                                                      Settings.SlicerLiteSettings.LastOpenedDirectory)
        if not dirPath:
            return
        self.loadInputData(dirPath)

        # self.loadDicomDirectory(r"C:\EDP-DATA\1-001\IRM pre et post avec contours xml")
        # self.loadDicomDirectory(r"C:\Kitware\Dicom\DataAnonymized2")

    def onClickLoadVolume(self):
        """
        User choose volume file to load
        """
        volumePath = qt.QFileDialog.getOpenFileName(self, "Load volume",
                                                    Settings.SlicerLiteSettings.LastOpenedDirectory,
                                                    "Image (*.nii, *.nii.gz, *mha, *nrrd)")
        if not volumePath:
            return

        self.loadInputData(volumePath)

    def loadInputData(self, inputPath: str):
        """
        Add and load the input dicom dir into the DICOM database
        directory_path: Path to the directory that contains dicom
        """
        qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)

        loadedVolumesNodes = []
        volumeNode = None

        if qt.QFileInfo(inputPath).isDir():
            Settings.SlicerLiteSettings.LastOpenedDirectory = inputPath
            loadedVolumesNodes = self.dataLoader.loadDicomDirInDBAndExtractVolumesAsItems(
                Settings.SlicerLiteSettings.LastOpenedDirectory)
        else:
            Settings.SlicerLiteSettings.LastOpenedDirectory = qt.QFileInfo(inputPath).absolutePath()
            hierarchy, volumeNode = self.dataLoader.loadVolume(inputPath)
            loadedVolumesNodes = [hierarchy]

        qt.QApplication.restoreOverrideCursor()

        if len(loadedVolumesNodes) == 0:
            return

        lastAddedItem = None
        for volumeNodeHierarchy in loadedVolumesNodes:
            nbDicomSlices = self.dataLoader.getNumberOfDicomFilesFromVolumeHierarchy(volumeNodeHierarchy)
            lastAddedItem = Model.VolumeItem(volumeNodeHierarchy, nbDicomSlices, volumeNode)
            index = self.itemTableModel.addItem(lastAddedItem)
            self.itemTableView.closePersistentEditor(index)

        if lastAddedItem:
            self.itemTableView.clearSelection()
            self.setCurrentVolumeItem(lastAddedItem)
            self.setCurrentSelectedLineOnTableView(self.itemTableModel.rowCount() - 1)

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
        if selectedRowId < 0 or selectedRowId >= self.itemTableModel.rowCount():
            return
        self.itemTableView.clearSelection()
        self.itemTableView.selectionModel().setCurrentIndex(self.itemTableModel.index(selectedRowId, 0),
                                                            qt.QItemSelectionModel.Select)

    def onDeleteVolumeItem(self, deletedVolumeName, deletedVolumeHierarchy):
        """
        Called after an item is deleted
        Set the current item to the first one
        """
        if self.itemTableModel.rowCount() <= 0:
            return
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
        if modelIndex.row() == self.lastSelectedRowIndex:
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
            minScalar = newItem.getMinScalarValue()
            maxScalar = newItem.getMaxScalarValue()
            range = maxScalar - minScalar
            # Reduce the scalar range to 80% to avoid full white or transparent volumes
            reducedRange = (1 - SlicerLiteSettings.DisplayScalarRange) / 2
            newMinimum = minScalar + reducedRange*range
            newMaximum = maxScalar - reducedRange*range
            self.shiftSliderWidget.minimum = newMinimum
            self.shiftSliderWidget.maximum = newMaximum
            self.shiftSliderWidget.blockSignals(True)
            self.shiftSliderWidget.setValue(newItem.shiftRenderingValue)
            self.shiftSliderWidget.blockSignals(False)
