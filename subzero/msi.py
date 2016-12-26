from distutils.command.bdist_msi import PyDialog


class AbstractDatabase(object):
    def __init__(self, db):
        self._db = db
        self._dialogs = []

    def add_dialog(self, dialog):
        self._dialogs.append(dialog)

    def commit(self):
        for dialog in self._dialogs:
            dialog.create(self._db)
        self._db.Commit()


class AttributesContainer(object):
    __Attributes = {}
    __Attribute = 0

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if value:
                self.__Attribute += self.__Attributes[key]


class AbstractDialog(AttributesContainer):
    __Attributes = {
        'Visible': 1,
        'Modal': 2,
        'Minimize': 4,
        'SysModal': 8,
        'KeepModeless': 16,
        'TrackDiskSpace': 32,
        'UseCustomPalette': 64,
        'RTLRO': 128,
        'RightAligned': 256,
        'LeftScroll': 512,
        'BiDi': 896,
        'Error': 65536,
    }

    def __init__(self, Dialog, HCentering, VCentering, Width, Height, Title, Control_First,
                 Control_Default, Control_Cancel, **kwargs):
        """
        :param Dialog:
        :param HCentering:
        :param VCentering:
        :param Width:
        :param Height:
        :param Title:
        :param Control_First:
        :param Control_Default:
        :param Control_Cancel:
        :param Visible:
        :param Modal:
        :param Minimize:
        :param SysModal:
        :param KeepModeless:
        :param TrackDiskSpace:
        :param UseCustomPalette:
        :param RTLRO:
        :param RightAligned:
        :param LeftScroll:
        :param BiDi:
        :param Error:
        """
        self._controls = []
        self._Dialog = Dialog
        self._HCentering = HCentering
        self._VCentering = VCentering
        self._Width = Width
        self._Height = Height
        self._Title = Title
        self._Control_First = Control_First
        self._Control_Default = Control_Default
        self._Control_Cancel = Control_Cancel

        super(AbstractDialog, self).__init__(**kwargs)

    def add_control(self, control):
        self._controls.append(control)

    def create(self, db):
        dialog = PyDialog(db, self.Dialog, self._HCentering, self._VCentering, self._Width, self._Height,
                          self._Attribute, self._Title, self._Control_First, self._Control_Default,
                          self._Control_Cancel, bitmap=False)
        for control in self._controls:
            control.create(dialog)


class AbstractControl(AttributesContainer):
    def __init__(self, **kwargs):
        self._events = []
        pass

    def add_event(self, event):
        self._events.append(event)

    def create(self, dialog):
        control = dialog.control()
        for event in self._events:
            event.create(control)


class AbstractEvent(AttributesContainer):
    def __init__(self, **kwargs):
        pass

    def create(self, control):
        event = control.event()
