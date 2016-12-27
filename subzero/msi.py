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
        :param Dialog: The primary key and name of the dialog box.
        :param HCentering: The horizontal position of the dialog box.
        The range is 0 to 100, with 0 at the left edge of the screen and 100 at the right edge.
        :param VCentering: The vertical position of the dialog box.
        The range is 0 to 100, with 0 at the top edge of the screen and 100 at the bottom edge.
        :param Width: The width of the rectangular boundary of the dialog box.
        This number must be non-negative.
        :param Height:The height of the rectangular boundary of the dialog box.
        This number must be non-negative.
        :param Title: A localizable text string specifying the title to be displayed in the title bar of the dialog box.
        :param Control_First: Combining this field with the Dialog field specifies a unique control
        in the Control Table that takes the focus when the dialog box is opened.
        :param Control_Default: Combining this field with the Dialog field specifies the default control that takes
        focus when the dialog box is opened.
        :param Control_Cancel: Combining this field with the Dialog field specifies a control that cancels
        the installation.
        :param Visible: If this bit is set the dialog is originally created as visible, otherwise it is hidden.
        :param Modal: If this bit is set, the dialog box is modal, other dialogs of the same application cannot be put
        on top of it, and the dialog keeps the control while it is running. If this bit is not set, the dialog is
        modeless, other dialogs of the same application may be moved on top of it. After a modeless dialog is created
        and displayed, the user interface returns control to the installer. The installer then calls the user interface
         periodically to update the dialog and to give it a chance to process the messages. As soon as this is done,
        the control is returned to the installer.
        :param Minimize: If this bit is set, the dialog box can be minimized. This bit is ignored for modal dialog
        boxes, which cannot be minimized.
        :param SysModal: If this style bit is set, the dialog box will stop all other applications and no other
        applications can take the focus. This state remains until the SysModal dialog is dismissed.
        :param KeepModeless: Normally, when this bit is not set and a dialog box is created through DoAction, all other
        (typically modeless) dialogs are destroyed. If this bit is set, the other dialogs stay alive when this dialog
        box is created.
        :param TrackDiskSpace: If this bit is set, the dialog box periodically calls the installer. If the property
        changes, it notifies the controls on the dialog. This style can be used if there is a control on the dialog
        indicating disk space. If the user switches to another application, adds or removes files, or otherwise
        modifies available disk space, you can quickly implement the change using this style.
        :param UseCustomPalette: If this bit is set, the pictures on the dialog box are created with the custom palette
        (one per dialog received from the first control created). If the bit is not set, the pictures are rendered
        using a default palette.
        :param RTLRO: If this style bit is set the text in the dialog box is displayed in right-to-left-reading order.
        :param RightAligned: If this style bit is set, the text is aligned on the right side of the dialog box.
        :param LeftScroll: If this style bit is set, the scroll bar is located on the left side of the dialog box.
        :param BiDi: This is a combination of the right to left reading order RTLRO, the RightAligned, and the
        LeftScroll dialog style bits.
        :param Error: If this bit is set, the dialog box is an error dialog.
        """
        self._controls = []
        self._Dialog = Dialog
        self._HCentering = HCentering
        self._VCentering = VCentering
        self._Width = Width
        self._Height = Height
        self._Title = Title
        self._Control_First = Control_First.Control
        self._Control_Default = Control_Default.Control
        self._Control_Cancel = Control_Cancel.Control

        super(AbstractDialog, self).__init__(**kwargs)

        added = []
        for ctrl in [Control_First, Control_Default, Control_Cancel]:
            if ctrl.Control not in added:
                added.append(ctrl.Control)
                self.add_control(ctrl)

    def add_control(self, control):
        self._controls.append(control)

    def create(self, db):
        dialog = PyDialog(db, self.Dialog, self._HCentering, self._VCentering, self._Width, self._Height,
                          self.__Attribute, self._Title, self._Control_First, self._Control_Default,
                          self._Control_Cancel, bitmap=False)
        for control in self._controls:
            control.create(dialog)


class AbstractControl(AttributesContainer):
    def __init__(self, Control, X, Y, Width, Height, Property=None, Text=None, Control_Next=None,
                 Help=None, **kwargs):
        self._events = []
        self._Control = Control
        self._X = X
        self._Y = Y
        self._Width = Width
        self._Height = Height
        self._Property = Property
        self._Text = Text
        self._Control_Next = Control_Next
        self._Help = Help

        super(AbstractControl, self).__init__(**kwargs)

    @property
    def Control(self):
        return self._Control

    def add_event(self, event):
        self._events.append(event)

    def create(self, dialog):
        control = dialog.control(self._Control, self._Type, self._X, self._Y, self._Width, self._Height,
                                 self.__Attribute, self._Property, self._Text, self._Control_Next, self.Help)
        for event in self._events:
            event.create(control)


class AbstractEvent(object):
    def __init__(self, event, argument, condition="1", ordering=None):
        """
        :param event:
        :param argument:
        :param condition:
        :param ordering:
        """
        self._event = event
        self._argument = argument
        self._condition = condition
        self._ordering = ordering

    def create(self, control):
        event = control.event(self._event, self._argument, self._condition, self._ordering)


class AbstractCondition(object):
    def __init__(self, event, attribute):
        self._event = event
        self._attribute = attribute

    def create(self, control):
        event = control.condition(self._event, self._attribute)
