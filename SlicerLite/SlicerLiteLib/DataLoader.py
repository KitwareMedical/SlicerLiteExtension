from typing import List

import qt, slicer
from DICOMLib import DICOMUtils
from .VolumeItemModel import VolumeHierarchy
from .SlicerUtils import *


class DataLoader():
    """
    Object responsible for loading a DICOM and notifying listeners on DICOM Load
    """
    def __del__(self):
        slicer.dicomDatabase.cleanup()

    def loadDicomDirInDBAndExtractVolumesAsItems(self, dicomDirectoryPath: str) -> List[VolumeHierarchy]:
        dicomWidget = getDicomWidget()
        dicomBrowser = dicomWidget.browserWidget.dicomBrowser
        dicomBrowser.importDirectory(dicomDirectoryPath, dicomBrowser.ImportDirectoryAddLink)

        loadedVolumeHierarchy = []

        db = slicer.dicomDatabase
        for patientUID in db.patients():
            for studyUID in db.studiesForPatient(patientUID):
                for seriesUID in db.seriesForStudy(studyUID):
                    volumeNodeID = DICOMUtils.loadSeriesByUID([seriesUID])
                    if len(volumeNodeID) > 0:
                        loadedVolumeHierarchy.append(VolumeHierarchy(patientUID, studyUID, seriesUID, volumeNodeID[0]))

        if len(loadedVolumeHierarchy) == 0:
            slicer.util.warningDisplay("No volume has been found from DICOM directory")
            return []

        return loadedVolumeHierarchy
