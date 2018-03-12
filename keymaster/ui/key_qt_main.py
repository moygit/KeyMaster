#!/usr/bin/env python3

"""Controller to handle communication between the main Qt form and the database.

pylint command-line:
pylint --max-line-length=120 --extension-pkg-whitelist=PyQt5 key_qt_main.py
"""

import sys

from PyQt5 import QtWidgets

from keymaster.key_password import PasswordDB
from keymaster.ui.key_qt_edit import EditController
from keymaster.ui.ui_main import Ui_main_form


_AVAILABLE_BASES = ["32", "64"]
_NICKNAMES_LIST_HEADER = "--Please select one of the following--"
_SELECTION_ERROR = "Please select a valid entry from the list of passwords."


class MainController(QtWidgets.QDialog):
    """Handle communication between the main Qt form and the database."""
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.ui = Ui_main_form()
        self.edit_form = EditController()
        self.pass_db, self.passwords_dic = None, None

    def start(self, pass_db=None, pass_dic=None):
        """Real initialization: ui, passwords-list, connect callbacks"""
        self.ui.setupUi(self)
        self.edit_form.start()
        self._connect_callbacks()
        if pass_db is None and pass_dic is None:
            self.pass_db, self.passwords_dic = self._get_data()
        else:
            self.pass_db, self.passwords_dic = pass_db, pass_dic
        if self.pass_db is None:
            sys.exit(-1)
        self._populate_pw_nicknames_list()

    def _get_data(self):
        """Create communications methods for the back-end get_data and call it."""
        def ask_to_create_new():
            """Ask user if we want to create a new password db."""
            msg_box = QtWidgets.QMessageBox()
            msg_box.setFont(self.font())
            msg_box.setText("Password database doesn't already exist.")
            msg_box.setInformativeText("Create a new one?")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            response = msg_box.exec_()
            return response == QtWidgets.QMessageBox.Yes
        def error_getting_db():
            """Notify user of error getting password database."""
            msg_box = QtWidgets.QMessageBox()
            msg_box.setFont(self.font())
            msg_box.setText("Error opening passwords db.  Exiting.")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()
            return
        return PasswordDB.get_data(ask_to_create_new, error_getting_db)

    def _populate_pw_nicknames_list(self):
        """Populate the main drop-down containing all password nicknames.
        According to how many items there are, decide which buttons
        on the form need to be enabled.
        """
        def _set_widgets_enabled(state):
            """Enable or disable widgets depending on whether we have data yet."""
            for widget in [self.ui.combobox_password_nicknames, self.ui.lineedit_enter_proto,
                           self.ui.button_get, self.ui.button_hint,
                           self.ui.button_update, self.ui.button_delete]:
                widget.setEnabled(state)
        nicknames = sorted(self.passwords_dic.keys())
        self.ui.combobox_password_nicknames.clear()
        if len(nicknames) > 1:  # add header and nicknames
            self.ui.combobox_password_nicknames.addItems([_NICKNAMES_LIST_HEADER])
        self.ui.combobox_password_nicknames.addItems(nicknames)
        if nicknames:   # have passwords, can do stuff with them
            _set_widgets_enabled(True)
            self.ui.lineedit_enter_proto.setFocus()
        else:           # no passwords yet, can only create new
            _set_widgets_enabled(False)
            self.ui.button_new.setFocus()


    def _connect_callbacks(self):
        """Connect ui events to callbacks."""
        self.ui.lineedit_enter_proto.returnPressed.connect(self.get_password)
        self.ui.checkbox_show_password.stateChanged.connect(self.toggle_show_password)
        self.ui.combobox_password_nicknames.currentIndexChanged.connect(self._clear_both)
        self.ui.button_get.clicked.connect(self.get_password)
        self.ui.button_hint.clicked.connect(self.get_hint)
        self.ui.button_new.clicked.connect(self.create_or_update_password)
        self.ui.button_update.clicked.connect(self.create_or_update_password)
        self.ui.button_delete.clicked.connect(self.delete_password)

    def _get_selected(self):
        """Figure out which password-nick they selected."""
        selected_text = str(self.ui.combobox_password_nicknames.currentText())
        if selected_text != _NICKNAMES_LIST_HEADER:
            return(self.ui.combobox_password_nicknames.currentIndex(), selected_text)
        return(0, None)

    # basic interactions with the main window:
    def _display_message(self, line_1, line_2):
        """Display the given message, lines 1 and 2."""
        self.ui.label_resp_header.setText(line_1)
        self.ui.label_resp_body.setText(line_2)
    def _display_error(self, error_message):
        """Display the given error."""
        self._display_message("<font color=red>ERROR</font>", "<font color=red>" + error_message + "</font>")
    def _clear_proto_passwords(self):
        """Clear the line where user enters proto-password."""
        self.ui.lineedit_enter_proto.setText("")
    def _clear_display(self):
        """Clear the main display line."""
        self._display_message('<font size="48">&nbsp;</font>', "")
    def _clear_both(self):
        """Clear both the user-entry line and the main display line."""
        self._clear_proto_passwords()
        self._clear_display()

    def get_password(self):
        """Get password for a particular selection."""
        self._clear_display()
        # get the selection:
        _, selection = self._get_selected()
        if not selection:
            self._display_error(_SELECTION_ERROR)
            return
        proto_pw_1 = str(self.ui.lineedit_enter_proto.text())
        password = self.passwords_dic[selection].calculate_password(proto_pw_1)
        self._display_message("Password copied to clipboard:", password)
        self.app.clipboard().setText(password)
        self.ui.combobox_password_nicknames.setFocus()

    def get_hint(self):
        """Look up the stored hint and display it."""
        # Get the selection:
        _, selection = self._get_selected()
        if not selection:
            self._display_error(_SELECTION_ERROR)
            return
        # Get the  hint, display it, and go to entry line-edit
        self._display_message("Hint is:", self.passwords_dic[selection].hint)
        self.ui.lineedit_enter_proto.setFocus()
        self.ui.lineedit_enter_proto.selectAll()

    def create_or_update_password(self):
        """
        Use same form either to create a new password or to update an
        existing password.
        """
        def get_password_from_user(is_update):
            """Create an entry form, validate user input, and return a Password object."""
            # If we're updating then populate the entry form with existing data to update:
            _, orig_nickname = self._get_selected()
            orig_pass = self.passwords_dic.get(orig_nickname, None)
            if is_update:
                if orig_pass:
                    self.edit_form.populate_form_from_password(orig_pass)
                else:
                    self._display_error(_SELECTION_ERROR)
                    return None, None
            else:
                self.edit_form.clear()

            # We'll keep showing the create-new-password window until we get good data.
            # (Unless the user cancels, in which case of course quit.)
            bad_data_entered = True     # Human-entered data is bad until we check it
            while bad_data_entered:
                # If the user cancels then quit.
                self.edit_form.ui.lineedit_nickname.setFocus()
                edit_return = self.edit_form.exec_()
                if not edit_return:
                    return None, None
                # Check for valid data: can't have either a blank nickname or one that already exists.
                nickname = str(self.edit_form.ui.lineedit_nickname.text())
                nickname_is_blank = nickname == ''
                nickname_already_exists = nickname in self.passwords_dic
                bad_data_entered = nickname_is_blank or (nickname_already_exists and not is_update)
                if bad_data_entered:
                    msg_box = QtWidgets.QMessageBox()
                    if nickname_is_blank:
                        msg_box.setText('Nickname cannot be blank. Please try again.')
                    if nickname_already_exists and not is_update:
                        msg_box.setText(nickname + ' already exists in password database. Please try again.')
                    msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
                    msg_box.setFont(self.font())
                    msg_box.exec_()
            return orig_nickname, self.edit_form.create_password_from_form()

        is_update = self.sender() == self.ui.button_update
        orig_nickname, password = get_password_from_user(is_update)
        if password is None:
            return
        # Either update the data-store or create a new password.
        if is_update:
            self.pass_db.update_old_password(orig_nickname, password)
            del self.passwords_dic[orig_nickname]
        else:
            self.pass_db.create_new_password(password)
        self.passwords_dic[password.nickname] = password
        self._populate_pw_nicknames_list()
        self._clear_both()
        return

    def delete_password(self, confirmed=False):
        """Respond to a request to delete a particular password.

        confirmed (default False) is a hack to allow testing without a confirmation messagebox.
        """
        def confirm_deletion(selection):
            """Confirm whether we want to delete."""
            msg_box = QtWidgets.QMessageBox()
            msg_box.setText('About to delete password "' + selection + '".')
            msg_box.setInformativeText('Are you sure?')
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msg_box.setFont(self.font())
            response = msg_box.exec_()
            return response == QtWidgets.QMessageBox.Yes

        # Clear the display:
        self._clear_both()
        # Get the selection:
        _, selection = self._get_selected()
        if not selection:
            self._display_error(_SELECTION_ERROR)
            return
        # Confirm and delete:
        if confirmed or confirm_deletion(selection):
            self.pass_db.delete_password(selection)
            del self.passwords_dic[selection]
            self._populate_pw_nicknames_list()
            self._display_message("STATUS:", selection + " has been deleted.")

    def reject(self):
        """User is dismissing the form.  Close up shop before closing app."""
        self.app.clipboard().setText('')
        self.pass_db.close_db()
        super().reject()

    def toggle_show_password(self):
        """Toggle whether or to display the password as it's typed."""
        if self.ui.checkbox_show_password.isChecked():
            self.ui.lineedit_enter_proto.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.ui.lineedit_enter_proto.setEchoMode(QtWidgets.QLineEdit.Password)


def main():
    """Really, pylint?"""
    app = QtWidgets.QApplication(sys.argv)
    main_form = MainController(app)
    main_form.start()
    main_form.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
