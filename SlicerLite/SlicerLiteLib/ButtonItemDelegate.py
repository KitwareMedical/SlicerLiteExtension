from enum import Enum
import qt, ctk

from .VolumeItemModel import *
from .Utils import Utils


class CustomUserRole(Enum):
    Visibility = qt.Qt.DisplayRole + 1


class ButtonItemDelegate(qt.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(ButtonItemDelegate, self).__init__(parent)
        self.current_selected_row = -1

    def getIcon(self, data):
        pass

    def onButtonClicked(self, model: qt.QAbstractItemModel, index: qt.QModelIndex):
        pass

    def isRowSelected(self, index: qt.QModelIndex):
        return self.current_selected_row == index.row()

    def getItem(self, index: qt.QModelIndex):
        return index.data(VolumeItemModel.ItemUserRole)

    def paint(self, painter: qt.QPainter, option: 'QStyleOptionViewItem', index: qt.QModelIndex):
        if self.isRowSelected(index):
            button = qt.QStyleOptionButton()
            button.rect = option.rect
            button.state = qt.QStyle.State_Enabled
            button.text = ""
            button.icon = self.getIcon(index)
            button.iconSize = qt.QSize(32, 32)
            qt.QApplication.style().drawControl(qt.QStyle.CE_PushButton, button, painter)

    def updateEditorGeometry(self, editor: qt.QWidget, option: 'QStyleOptionViewItem', index: qt.QModelIndex):
        editor.setGeometry(option.rect)

    def editorEvent(self, event: qt.QEvent, model: qt.QAbstractItemModel, option: 'QStyleOptionViewItem',
                    index: qt.QModelIndex) -> bool:
        if event.type() == qt.QEvent.MouseButtonRelease and self.isRowSelected(index):
            self.onButtonClicked(model, index)
        return True


class DeleteButtonItemDelegate(ButtonItemDelegate):
    def getIcon(self, index):
        return Utils.getIcon("close")

    def onButtonClicked(self, model: qt.QAbstractItemModel, index: qt.QModelIndex):
        item = self.getItem(index)
        model.removeRow(index.row())
        del item


class DicomMetadataButtonItemDelegate(ButtonItemDelegate):
    def getIcon(self, index):
        return Utils.getIcon("metadata")

    def onButtonClicked(self, model: qt.QAbstractItemModel, index: qt.QModelIndex):
        from .DataLoader import DataLoader

        item = self.getItem(index)
        dicom_widget = getDicomWidget()
        dicom_browser = dicom_widget.browserWidget.dicomBrowser
        dicom_browser.dicomTableManager().setCurrentPatientsSelection([item.volumeHierarchy.patientUID])
        dicom_browser.dicomTableManager().setCurrentStudiesSelection([item.volumeHierarchy.studyUID])
        dicom_browser.dicomTableManager().setCurrentSeriesSelection([item.volumeHierarchy.seriesUID])

        dicom_browser.showMetadata(dicom_browser.fileListForCurrentSelection(ctk.ctkDICOMModel.SeriesType))