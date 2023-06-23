from typing import List

import qt, slicer
from DICOMLib import DICOMUtils
from .ItemModel import DICOMItem


class DataLoader():
    """
    Object responsible for loading a DICOM and notifying listeners on DICOM Load
    """
    def __del__(self):
        slicer.dicomDatabase.cleanup()

    def loadDicomDirInDBAndExtractVolumesAsItems(self, dicomDirectoryPath: str) -> List[DICOMItem]:
        dicomWidget = self.getDicomWidget()
        dicomBrowser = dicomWidget.browserWidget.dicomBrowser
        dicomBrowser.importDirectory(dicomDirectoryPath, dicomBrowser.ImportDirectoryAddLink)

        loadedDicomItems = []

        db = slicer.dicomDatabase
        for patientUID in db.patients():
            for studyUID in db.studiesForPatient(patientUID):
                for seriesUID in db.seriesForStudy(studyUID):
                    volumeNodeID = DICOMUtils.loadSeriesByUID([seriesUID])
                    if len(volumeNodeID) > 0:
                        loadedDicomItems.append(DICOMItem(patientUID, studyUID, seriesUID, volumeNodeID[0]))

        if len(loadedDicomItems) == 0:
            slicer.util.warningDisplay("No volume has been found from DICOM directory")
            return []

        return loadedDicomItems

    @staticmethod
    def getDicomWidget():
        try:
            return slicer.modules.DICOMWidget
        except AttributeError:
            return slicer.modules.dicom.widgetRepresentation().self()