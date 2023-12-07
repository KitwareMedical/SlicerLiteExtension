import qt


class IterableAttributeMeta(type):
    """
    Metaclass allowing to iterate on the public attributes.
    """

    def __iter__(self):
        for attr in dir(self):
            if not attr.startswith("__"):
                yield attr

    def __getitem__(self, attr):
        if not attr.startswith("__"):
            return getattr(self, attr)


class DefaultSettings(metaclass=IterableAttributeMeta):
    """
    Default settings of the application.
    Each setting will be accessible through SlicerLite/{parameter_name}
    """
    LastOpenedDirectory = ""
    DisplayScalarRange = 0.8


class SettingsMeta(type):
    """
    Meta type for the application settings.
    Initializes the .ini settings if they are not present and converts the values to float by default.
    """

    def __new__(mcs, *args, **kwargs):
        x = super().__new__(mcs, *args, **kwargs)
        for k in DefaultSettings:
            if not qt.QSettings().contains(f"SlicerLite/{k}"):
                qt.QSettings().setValue(f"SlicerLite/{k}", DefaultSettings[k])
        return x

    def __dir__(self):
        return [k for k in DefaultSettings]

    def __getattr__(cls, attr):
        if attr not in DefaultSettings:
            raise AttributeError(f"Class doesn't contain {attr}")
        value = qt.QSettings().value(f"SlicerLite/{attr}")
        try:
            defaultType = type(getattr(DefaultSettings, attr))
            return defaultType(value)
        except ValueError:
            return value

    def __setattr__(self, key, value):
        if key not in DefaultSettings:
            raise AttributeError(f"Class doesn't contain {key}")
        qt.QSettings().setValue(f"SlicerLite/{key}", value)


class SlicerLiteSettings(metaclass=SettingsMeta):
    """
    Class managing the settings of the application.
    The settings are read from Settings/DefaultSettings.ini file.
    """
    pass
