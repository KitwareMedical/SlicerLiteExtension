from enum import Enum
import qt, ctk

from .VolumeItemModel import *
from .Utils import *


class ButtonItemDelegate(qt.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(ButtonItemDelegate, self).__init__(parent)
        self.current_selected_row = -1

    def getIcon(self):
        pass

    def onButtonClicked(self, model: qt.QAbstractItemModel, index: qt.QModelIndex):
        pass

    def isRowSelected(self, index: qt.QModelIndex):
        return self.current_selected_row == index.row()

    def getItem(self, index: qt.QModelIndex):
        return index.data(VolumeItemModel.ItemUserRole)

    def createEditor(self, parent, option, index):
        if index.column() in (1, 2):
            button = qt.QPushButton(parent)
            button.icon = self.getIcon()
            button.iconSize = qt.QSize(22, 22)
            button.clicked.connect(lambda _:self.onButtonClicked(index.model(), index))
            return button

    def updateEditorGeometry(self, editor: qt.QWidget, option: 'QStyleOptionViewItem', index: qt.QModelIndex):
        if editor:
            editor.setGeometry(option.rect)


class DeleteButtonItemDelegate(ButtonItemDelegate):
    def getIcon(self):
        return getIcon("close")

    def onButtonClicked(self, model: qt.QAbstractItemModel, index: qt.QModelIndex):
        item = self.getItem(index)
        model.removeRow(index.row())
        del item


class DicomMetadataButtonItemDelegate(ButtonItemDelegate):
    def getIcon(self):
        return getIcon("metadata")

    def onButtonClicked(self, model: qt.QAbstractItemModel, index: qt.QModelIndex):
        item = self.getItem(index)
        dicom_widget = getDicomWidget()
        dicom_browser = dicom_widget.browserWidget.dicomBrowser
        dicom_browser.dicomTableManager().setCurrentPatientsSelection([item.volumeHierarchy.patientUID])
        dicom_browser.dicomTableManager().setCurrentStudiesSelection([item.volumeHierarchy.studyUID])
        dicom_browser.dicomTableManager().setCurrentSeriesSelection([item.volumeHierarchy.seriesUID])

        dicom_browser.showMetadata(dicom_browser.fileListForCurrentSelection(ctk.ctkDICOMModel.SeriesType))