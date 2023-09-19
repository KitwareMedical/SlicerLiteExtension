from typing import List

import qt, slicer
from DICOMLib import DICOMUtils
from SlicerLiteLib import Model, SlicerUtils


class DicomDataLoader():
    """
    Object responsible for loading a DICOM and notifying listeners on DICOM Load
    """
    def __init__(self):
        self.alreadyLoadedVolumeHierarchy = []
        self.database = None

    def __del__(self):
        DICOMUtils.closeTemporaryDatabase(self.database.originalDatabaseDir)

    def volumeDeleted(self, deletedVolumeName: str, deletedVolumeHierarchy: Model.VolumeHierarchy):
        """
        Slot called whe a VolumeItem is deleted
        """
        self.alreadyLoadedVolumeHierarchy.remove(deletedVolumeHierarchy)

    def loadDicomDirInDBAndExtractVolumesAsVolumeHierarchy(self, dicomDirectoryPath: str) -> List[Model.VolumeHierarchy]:
        loadedVolumeHierarchy = []

        if not self.database:
            # Define slicer.dicomDatabase as the created temporary database
            # Initilize here because else, it's called earlier during slicer starts
            self.database = DICOMUtils.openTemporaryDatabase()

        db = slicer.dicomDatabase
        DICOMUtils.importDicom(dicomDirectoryPath, db)
        for patientUID in db.patients():
            for studyUID in db.studiesForPatient(patientUID):
                for seriesUID in db.seriesForStudy(studyUID):
                    seriesDescription = db.descriptionForSeries(seriesUID)
                    if not self.isVolumeItemHierarchyAlreadyAdded(patientUID, studyUID, seriesUID, seriesDescription):
                        volumeNodeID = DICOMUtils.loadSeriesByUID([seriesUID])
                        if len(volumeNodeID) > 0:
                            loadedVolumeHierarchy.append(Model.VolumeHierarchy(patientUID, studyUID, seriesUID, volumeNodeID[0], seriesDescription))

        if len(loadedVolumeHierarchy) == 0:
            slicer.util.warningDisplay("No volume has been found from DICOM directory or volume already added.")
            return []

        self.alreadyLoadedVolumeHierarchy = self.alreadyLoadedVolumeHierarchy + loadedVolumeHierarchy
        return loadedVolumeHierarchy

    def getNumberOfDicomFilesFromVolumeHierarchy(self, volumeHierarchy):
        """
        Get the number of files associated to a volume
        """
        return len(slicer.dicomDatabase.instancesForSeries(volumeHierarchy.seriesUID))

    def isVolumeItemHierarchyAlreadyAdded(self, patientUID, studyUID, seriesUID, description):
        """
        Check if the input VolumeHierarchy has already been added before
        """
        for volumeItem in self.alreadyLoadedVolumeHierarchy:
            if volumeItem.patientUID == patientUID and \
                    volumeItem.studyUID == studyUID and \
                    volumeItem.seriesUID == seriesUID and \
                    volumeItem.seriesDescription == description:
                return True
        return False
