from typing import List

import qt, slicer
from DICOMLib import DICOMUtils
from .ItemModel import DICOMItem


class DataLoader(object):
    """
    Object responsible for loading a DICOM and notifying listeners on DICOM Load
    """
    def __init__(self):
        pass

    def __del__(self):
        slicer.dicomDatabase.cleanup()

    def load_dicom_dir_in_db_and_extract_volumes_as_items(self, dicomDirectoryPath: str) -> List[DICOMItem]:
        dicomWidget = self.get_dicom_widget()
        dicomBrowser = dicomWidget.browserWidget.dicomBrowser
        dicomBrowser.importDirectory(dicomDirectoryPath, dicomBrowser.ImportDirectoryAddLink)

        loaded_dicom_items = []

        db = slicer.dicomDatabase
        for patientUID in db.patients():
            for studyUID in db.studiesForPatient(patientUID):
                for seriesUID in db.seriesForStudy(studyUID):
                    volumeNodeID = DICOMUtils.loadSeriesByUID([seriesUID])
                    if len(volumeNodeID) > 0:
                        loaded_dicom_items.append(DICOMItem(patientUID, studyUID, seriesUID, volumeNodeID[0]))

        if len(loaded_dicom_items) == 0:
            slicer.util.warningDisplay("No volume has been found from DICOM directory")
            return []

        return loaded_dicom_items

    @staticmethod
    def get_dicom_widget():
        try:
            dicomWidget = slicer.modules.DICOMWidget
        except AttributeError:
            dicomWidget = slicer.modules.dicom.widgetRepresentation().self()
        return dicomWidget