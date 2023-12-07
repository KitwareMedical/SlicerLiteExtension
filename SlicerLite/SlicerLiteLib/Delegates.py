from enum import Enum
import qt
import ctk

from SlicerLiteLib import Model, Utils, SlicerUtils


def getItem(index: qt.QModelIndex):
    return index.data(Model.VolumeItemModel.ItemUserRole)


class ButtonItemDelegate(qt.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(ButtonItemDelegate, self).__init__(parent)

    def getIcon(self):
        pass

    def onButtonClicked(self, model: qt.QAbstractItemModel, index: qt.QModelIndex):
        pass

    def sizeHint(self, option: qt.QStyleOptionViewItem, index: qt.QModelIndex):
        return qt.QSize(22, 22)

    def createEditor(self, parent, option, index):
        if index.column() not in (1, 2):
            return None

        button = qt.QPushButton(parent)
        button.icon = self.getIcon()
        button.iconSize = qt.QSize(22, 22)
        button.setMinimumSize(qt.QSize(22, 22))
        button.clicked.connect(lambda _: self.onButtonClicked(index.model(), index))
        return button

    def updateEditorGeometry(self, editor: qt.QWidget, option: 'QStyleOptionViewItem', index: qt.QModelIndex):
        if editor:
            editor.setGeometry(option.rect)


class DeleteButtonItemDelegate(ButtonItemDelegate):

    def __init__(self, parent=None):
        super(DeleteButtonItemDelegate, self).__init__(parent)
        self.modelDeletedSignal = Utils.Signal()

    def getIcon(self):
        return Utils.getIcon("delete")

    def onButtonClicked(self, model: qt.QAbstractItemModel, index: qt.QModelIndex):
        item = getItem(index)
        volumeName = item.volumeName
        volumeHierarchy = item.volumeHierarchy
        model.removeRow(index.row())
        del item
        self.modelDeletedSignal.emit(volumeName, volumeHierarchy)


class DicomMetadataButtonItemDelegate(ButtonItemDelegate):

    def createEditor(self, parent, option, index):
        if not index.model().getVolumeItemFromId(index.row()).isDicomVolumeItem():
            return
        return super().createEditor(parent, option, index)

    def getIcon(self):
        return Utils.getIcon("metadata")

    def onButtonClicked(self, model: qt.QAbstractItemModel, index: qt.QModelIndex):
        item = getItem(index)
        dicom_widget = SlicerUtils.getDicomWidget()
        dicom_browser = dicom_widget.browserWidget.dicomBrowser
        dicom_browser.dicomTableManager().setCurrentPatientsSelection([item.volumeHierarchy.patientUID])
        dicom_browser.dicomTableManager().setCurrentStudiesSelection([item.volumeHierarchy.studyUID])
        dicom_browser.dicomTableManager().setCurrentSeriesSelection([item.volumeHierarchy.seriesUID])

        dicom_browser.showMetadata(dicom_browser.fileListForCurrentSelection(ctk.ctkDICOMModel.SeriesType))
