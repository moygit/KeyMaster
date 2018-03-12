#!/usr/bin/env python3

"""Controller for the Qt interface for (editing) password objects.

pylint command-line:
pylint --max-line-length=120 --extension-pkg-whitelist=PyQt5 key_qt_edit.py
"""

import sys
from PyQt5 import QtCore, QtWidgets
from keymaster.key_password import Password
from keymaster.ui.ui_edit import Ui_edit_form


_AVAILABLE_BASES = ["32", "64"]


class EditController(QtWidgets.QDialog):
    """Controller for the Qt interface for password objects."""
    def __init__(self):
        super().__init__()
        self.ui = Ui_edit_form()
        self.ui.setupUi(self)
        self.orig_nick = ""
        self.update_flag = False
        self.dirty_flag = False
        self.setWindowTitle("Create new password object")

    def start(self):
        """Real initialization: ui and callbacks"""
        self.ui.combobox_base.addItems(_AVAILABLE_BASES)
        self.ui.spinbox_iteration.valueChanged.connect(self.set_dirty)
        for lineedit in [self.ui.lineedit_nickname, self.ui.lineedit_username,
                         self.ui.lineedit_hostname, self.ui.lineedit_hint]:
            lineedit.textChanged.connect(self.set_dirty)
        self.ui.spinbox_substring_start.valueChanged.connect(self.set_dirty)
        self.ui.spinbox_substring_end.valueChanged.connect(self.set_dirty)
        self.ui.combobox_base.currentIndexChanged.connect(self.base_changed)
        self.ui.checkbox_special_char.stateChanged.connect(self.special_char_changed)
        self.ui.edit_buttons.accepted.connect(self.confirm_accept)
        self.ui.edit_buttons.rejected.connect(self.reject)
        self.ui.lineedit_nickname.setFocus()

    def clear(self):
        self.orig_nick = ""
        self.ui.lineedit_nickname.clear()
        self.ui.lineedit_username.clear()
        self.ui.lineedit_hostname.clear()
        self.ui.lineedit_hint.clear()
        self.ui.spinbox_iteration.setValue(1)
        self.ui.spinbox_substring_start.setValue(0)
        self.ui.spinbox_substring_end.setValue(15)
        self.ui.combobox_base.setCurrentIndex(0)
        self.ui.checkbox_special_char.setChecked(False)

    def special_char_changed(self, new_state):
        """The flag denoting whether we use special chars has changed.
        This also affects whether we're in base-32 mode or base-64,
        plus since something's changed we should set the dirty flag
        as well.
        """
        self.set_dirty()
        # 64-bit strings use '/' and '+', so if special characters are
        # not allowed then we have to use 32-bit strings:
        if new_state == QtCore.Qt.Unchecked:
            base32_index = self.ui.combobox_base.findText("32")
            self.ui.combobox_base.setCurrentIndex(base32_index)

    def base_changed(self, new_state):
        """base-32 vs. base-64 has changed.  Set the dirty flag
        and also change whether we use special characters.
        """
        self.set_dirty()
        # 64-bit strings use '/' and '+', so special characters are
        # required:
        if new_state == self.ui.combobox_base.findText("64"):
            self.ui.checkbox_special_char.setChecked(True)

    def confirm_accept(self):
        """Updates are dangerous so we confirm with user."""
        if self.update_flag and self.dirty_flag:
            msg_box = QtWidgets.QMessageBox()
            upd_msg = 'About to update password "%s".'
            msg_box.setText(upd_msg % self.orig_nick)
            msg_box.setInformativeText('Are you sure?')
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msg_box.setFont(self.font())
            response = msg_box.exec_()
            del msg_box
            if response == QtWidgets.QMessageBox.Yes:
                self.accept()
            else:
                self.reject()
        else:
            self.accept()

    def set_dirty(self):
        """dirty flag tells us whether any changes have been made."""
        self.dirty_flag = True

    def populate_form_from_password(self, pw_obj):
        """Populate myself with info from existing Password object."""
        self.orig_nick = pw_obj.nickname
        self.ui.lineedit_nickname.setText(pw_obj.nickname)
        self.ui.lineedit_username.setText(pw_obj.username)
        self.ui.lineedit_hostname.setText(pw_obj.hostname)
        self.ui.checkbox_special_char.setChecked(pw_obj.special_char)
        self.ui.combobox_base.setCurrentIndex(self.ui.combobox_base.findText(str(pw_obj.base)))
        self.ui.spinbox_iteration.setValue(pw_obj.iteration)
        self.ui.lineedit_hint.setText(pw_obj.hint)
        self.ui.spinbox_substring_start.setValue(pw_obj.start)
        self.ui.spinbox_substring_end.setValue(pw_obj.finish)
        self.update_flag = True

    def create_password_from_form(self):
        """Convert the info we're holding into a Password object."""
        return Password(
            str(self.ui.lineedit_nickname.text()),
            str(self.ui.lineedit_username.text()),
            str(self.ui.lineedit_hostname.text()),
            self.ui.checkbox_special_char.isChecked(),
            int(self.ui.combobox_base.currentText()),
            int(self.ui.spinbox_iteration.value()),
            str(self.ui.lineedit_hint.text()),
            int(self.ui.spinbox_substring_start.value()),
            int(self.ui.spinbox_substring_end.value()))


def main():
    """Really, pylint?"""
    _ = QtWidgets.QApplication(sys.argv)
    edit_form = EditController()
    edit_form.start()
    edit_form.show()
    ret = edit_form.exec_()
    print("Dirty flag: " + str(edit_form.dirty_flag))
    print("Update flag: " + str(edit_form.update_flag))
    print("Return value: " + str(ret))
    sys.exit(ret)


if __name__ == "__main__":
    main()
