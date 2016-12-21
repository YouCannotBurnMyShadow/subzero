from distutils.command.bdist_msi import PyDialog


class AbstractDatabase(object):
    def __init__(self, db):
        self._db = db

    def add_dialog(self, dialog):
        PyDialog(self.db, 'FilesInUse',
                 self.x, self.y, self.width, self.height, 19, self.title,
                 'Retry', 'Retry', 'Retry', bitmap=False)

        # 1. Create dialog using py_args and py_kwargs
        # 2. Iterate through py_controls and create each control with events


class AbstractDialog(object):
    def __init__(self, Dialog, HCentering, VCentering, Width, Height, Attributes, Title, Control_First,
                 Control_Default, Control_Cancel):
        self._controls = []
        pass

    @property
    def py_args(self):
        pass

    @property
    def py_kwargs(self):
        pass

    @property
    def py_controls(self):
        return self._controls

    def add_control(self, control):
        self._controls.append(control)


class AbstractControl(object):
    def __init__(self, **kwargs):
        pass

    @property
    def py_args(self):
        pass

    @property
    def py_kwargs(self):
        pass
