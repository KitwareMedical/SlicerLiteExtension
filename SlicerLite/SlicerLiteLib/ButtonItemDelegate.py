from enum import Enum
import qt, ctk

from .ItemModel import *
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

    def is_row_selected(self, index: qt.QModelIndex):
        return self.current_selected_row == index.row()

    def get_item(self, index: qt.QModelIndex):
        return index.data(ItemModel.ItemUserRole)

    def paint(self, painter: qt.QPainter, option: 'QStyleOptionViewItem', index: qt.QModelIndex) -> None:
        if self.is_row_selected(index):
            button = qt.QStyleOptionButton()
            button.rect = option.rect
            button.state = qt.QStyle.State_Enabled
            button.text = ""
            button.icon = self.getIcon(index)
            button.iconSize = qt.QSize(32, 32)
            qt.QApplication.style().drawControl(qt.QStyle.CE_PushButton, button, painter)

    def updateEditorGeometry(self, editor: qt.QWidget, option: 'QStyleOptionViewItem', index: qt.QModelIndex) -> None:
        editor.setGeometry(option.rect)

    def editorEvent(self, event: qt.QEvent, model: qt.QAbstractItemModel, option: 'QStyleOptionViewItem',
                    index: qt.QModelIndex) -> bool:
        if event.type() == qt.QEvent.MouseButtonRelease and self.is_row_selected(index):
            self.onButtonClicked(model, index)
        return True


class DeleteButtonItemDelegate(ButtonItemDelegate):
    def __init__(self, parent=None):
        super(DeleteButtonItemDelegate, self).__init__(parent)

    def getIcon(self, index):
        return Utils.getIcon("delete")

    def onButtonClicked(self, model: qt.QAbstractItemModel, index: qt.QModelIndex):
        item = self.get_item(index)
        model.removeRow(index.row())
        del item


class DicomMetadataButtonItemDelegate(ButtonItemDelegate):
    def __init__(self, parent=None):
        super(DicomMetadataButtonItemDelegate, self).__init__(parent)

    def getIcon(self, index):
        return Utils.getIcon("metadata")

    def onButtonClicked(self, model: qt.QAbstractItemModel, index: qt.QModelIndex):
        from .DataLoader import DataLoader

        item = self.get_item(index)
        dicom_widget = DataLoader.get_dicom_widget()
        dicom_browser = dicom_widget.browserWidget.dicomBrowser
        dicom_browser.dicomTableManager().setCurrentPatientsSelection([item.dicomItem.patientUID])
        dicom_browser.dicomTableManager().setCurrentStudiesSelection([item.dicomItem.studyUID])
        dicom_browser.dicomTableManager().setCurrentSeriesSelection([item.dicomItem.seriesUID])

        dicom_browser.showMetadata(dicom_browser.fileListForCurrentSelection(ctk.ctkDICOMModel.SeriesType))