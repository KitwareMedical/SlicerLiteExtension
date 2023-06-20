#-----------------------------------------------------------------------------
set(MODULE_NAME SlicerLite)

#-----------------------------------------------------------------------------
set(LIB_NAME SlicerLitelib)
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  ${LIB_NAME}/ButtonItemDelegate.py
  ${LIB_NAME}/DataLoader.py
  ${LIB_NAME}/EventFilters.py
  ${LIB_NAME}/ItemModel.py
  ${LIB_NAME}/SlicerLiteModuleWidget.py
  ${LIB_NAME}/SlicerUtils.py
  ${LIB_NAME}/UIUtils.py
  ${LIB_NAME}/Utils.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/Icons/delete.png
  Resources/Icons/metadata.png
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
