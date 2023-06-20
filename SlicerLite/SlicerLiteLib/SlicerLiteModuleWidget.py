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

        self.data_loader = DataLoader()
        self.item_table_model = ItemModel()
        self.item_table_view = qt.QTableView()
        self.delete_button_item_delegate = DeleteButtonItemDelegate()
        self.dicom_tags_button_item_delegate = DicomMetadataButtonItemDelegate()

        self.buttons_delegate = [self.delete_button_item_delegate, self.dicom_tags_button_item_delegate]

        # Setup event filter
        self.filter = DragAndDropEventFilter(slicer.util.mainWindow(), self.load_dicom_directory)
        slicer.util.mainWindow().installEventFilter(self.filter)

        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Create and initialize UI components
        """
        self.setup_table_view_layout()
        self.setup_rendering_layout()
        self.setup_segmentation_layout()
        self.layout().addStretch()

    def setup_table_view_layout(self) -> None:
        """
        Setup the table view behavior/display
        """
        self.item_table_view.setItemDelegateForColumn(1, self.dicom_tags_button_item_delegate)
        self.item_table_view.setItemDelegateForColumn(2, self.delete_button_item_delegate)
        # Hide headers
        self.item_table_view.horizontalHeader().hide()
        self.item_table_view.verticalHeader().hide()
        # Hide table borders
        self.item_table_view.setFrameStyle(qt.QFrame.NoFrame)
        self.item_table_view.horizontalHeader().setSectionResizeMode(qt.QHeaderView.Stretch)
        self.item_table_view.horizontalHeader().resizeSection(1, 32)
        self.item_table_view.horizontalHeader().resizeSection(2, 32)
        # Make lines no editabled
        self.item_table_view.setEditTriggers(qt.QAbstractItemView.NoEditTriggers)
        # Allow only one selection
        self.item_table_view.setSelectionMode(qt.QAbstractItemView.SingleSelection)

        self.item_table_view.clicked.connect(self.on_table_view_item_clicked)
        self.item_table_view.setModel(self.item_table_model)

        self.layout().addWidget(UIUtils.createButton("Load", callback=self.on_click_load_dicom_directory))
        self.layout().addWidget(qt.QLabel("Loaded volumes:"))
        self.layout().addWidget(self.item_table_view)

    def setup_rendering_layout(self) -> None:
        """
        Get and place shift rendering sliders for volume rendering
        """
        self.rendering_module = slicer.util.getNewModuleGui(slicer.modules.volumerendering)
        self.shift_slider_widget = slicer.util.findChild(self.rendering_module, "PresetOffsetSlider")
        self.shift_slider_widget.setEnabled(False)

        layout = qt.QHBoxLayout()
        layout.addWidget(qt.QLabel("Rendering shift:"))
        layout.addWidget(self.shift_slider_widget)

        self.layout().addLayout(layout)

    def setup_segmentation_layout(self) -> None:
        """
        Get and set the segmentation modules and simplify it
        """
        segment_editor_module = slicer.modules.segmenteditor.widgetRepresentation()
        self.segment_editor_widget = slicer.util.findChild(segment_editor_module, "qMRMLSegmentEditorWidget")
        self.layout().addWidget(UIUtils.wrapInCollapsibleButton(segment_editor_module, "Segmentation"))

        # Define list of hidden widgets inside segment editor widget
        hidden_widgets_names = ["SourceVolumeNodeLabel", "SourceVolumeNodeComboBox",
                                "SegmentationNodeLabel", "SegmentationNodeComboBox",
                                "SpecifyGeometryButton", "SwitchToSegmentationsButton"]
        add_segmentation_button = None
        for widget in self.segment_editor_widget.children():
            if hasattr(widget, "objectName"):
                if widget.objectName in hidden_widgets_names:
                    widget.setVisible(False)
                if widget.objectName == "AddSegmentButton":
                    add_segmentation_button = widget

        # Need to add a new slot in order to avoid 3DSlicer to update this button visibility when adding a new segment
        if add_segmentation_button:
            add_segmentation_button.clicked.connect(self.segment_editor_widget.rotateSliceViewsToSegmentation)

    def on_click_load_dicom_directory(self) -> None:
        """
        User choose directory where DICOM will be extracted
        """
        dirPath = qt.QFileDialog.getExistingDirectory(self,
                                                     "Choose dicom file directory to load",
                                                     self._lastOpenedDirectory)
        if not dirPath:
            return
        self.load_dicom_directory(dirPath)

    def load_dicom_directory(self, directory_path: str) -> None:
        """
        Add and load the input dicom dir into the DICOM database
        directory_path: Path to the directory that contains dicoms
        """
        qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)

        self._lastOpenedDirectory = directory_path
        loadedVolumesNodes = self.data_loader.load_dicom_dir_in_db_and_extract_volumes_as_items(self._lastOpenedDirectory)
        for volumeNode in loadedVolumesNodes:
            self.item_table_model.add_item(Item(volumeNode))

        qt.QApplication.restoreOverrideCursor()

        # Don't show anything in slices
        SlicerUtils.show_volume_as_foreground_in_slices(None)
        SlicerUtils.show_volume_as_background_in_slices(None)
        self.item_table_view.clearSelection()

    def set_current_item(self, item: Item) -> None:
        """
        Set the current item to the corresponding modules
        """
        self.rendering_module.setMRMLVolumeNode(item.volumeNode if item else None)
        self.shift_slider_widget.setEnabled(bool(item.volumeNode) if item else False)
        self.segment_editor_widget.setSegmentationNode(item.segmentationNode if item else None)
        self.segment_editor_widget.setSourceVolumeNode(item.volumeNode if item else None)
        if item:
            self.segment_editor_widget.rotateSliceViewsToSegmentation()

    def on_table_view_item_clicked(self, modelIndex: qt.QModelIndex) -> None:
        """
        Update views and current item according to the clicked item
        """
        if not modelIndex.model():
            SlicerUtils.show_volume_as_foreground_in_slices(None)
            SlicerUtils.show_volume_as_background_in_slices(None)
            self.item_table_view.clearSelection()
            self.set_current_item(None)
            return

        item = modelIndex.model().item(modelIndex.row()).data(ItemModel.ItemUserRole)
        # We only want to select line if user click on volume's name
        if modelIndex.column() != 0:
            return

        self.set_current_item(item)
        for button_delegate in self.buttons_delegate:
            button_delegate.current_selected_row = modelIndex.row()
        modelIndex.model().toggle_volume_visibility(modelIndex.row())

    def on_delete_item(self):
        self.item_table_model.viewport().update()

