#!/usr/bin/env python3

"""Basic usage unit-tests for the edit form."""

import sys

from PyQt5 import QtWidgets
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from keymaster.key_password import Password
from keymaster.ui.key_qt_edit import EditController

APP = QtWidgets.QApplication(sys.argv)


def test_do_nothing():
    """Just create the form and press ok."""
    # Given:
    form = EditController()
    form.start()
    # When we do nothing:
    ok_button = form.ui.edit_buttons.button(form.ui.edit_buttons.Ok)
    QTest.mouseClick(ok_button, Qt.LeftButton)
    # Then check defaults and form returns 1 because we ok'ed:
    assert not form.dirty_flag
    assert not form.update_flag
    assert form.result() == 1


def test_toggle_special_chars():
    """Toggle the special-chars checkbox and press cancel."""
    # Given:
    form = EditController()
    form.start()
    # When we toggle the special-chars checkbox:
    form.ui.checkbox_special_char.setChecked(True)
    cancel_button = form.ui.edit_buttons.button(form.ui.edit_buttons.Cancel)
    QTest.mouseClick(cancel_button, Qt.LeftButton)
    # Then dirty-flag is set and form returns 0 b/c we cancelled:
    assert form.dirty_flag
    assert not form.update_flag
    assert form.result() == 0


def test_change_nickname():
    """Change the nickname and press cancel."""
    # Given:
    form = EditController()
    form.start()
    # When we edit the nickname:
    form.ui.lineedit_nickname.setText("junk")
    cancel_button = form.ui.edit_buttons.button(form.ui.edit_buttons.Cancel)
    QTest.mouseClick(cancel_button, Qt.LeftButton)
    # Then dirty-flag is set:
    assert form.dirty_flag


def test_create():
    """Create a new password."""
    # Given:
    form = EditController()
    form.start()
    nick, user, host, iteration, hint = "nick", "user", "host.com", 3, "hint"
    # When we create a new pw:
    form.ui.lineedit_nickname.setText(nick)
    form.ui.lineedit_username.setText(user)
    form.ui.lineedit_hostname.setText(host)
    form.ui.spinbox_iteration.setValue(iteration)
    form.ui.lineedit_hint.setText(hint)
    ok_button = form.ui.edit_buttons.button(form.ui.edit_buttons.Ok)
    QTest.mouseClick(ok_button, Qt.LeftButton)
    password = form.create_password_from_form()
    # Then we get that new pw back:
    assert form.dirty_flag
    assert not form.update_flag
    assert form.result() == 1
    assert password == Password(nickname=nick, username=user, hostname=host, iteration=iteration, hint=hint)


def test_base_and_special_chars():
    """Verify that base == 64 implies special-chars."""
    # Given:
    form = EditController()
    form.start()
    # When we set the base to 64:
    form.ui.combobox_base.setCurrentText("64")
    # Then we must have special chars:
    assert form.ui.checkbox_special_char.isChecked() == True
    # When we unset special chars:
    form.ui.checkbox_special_char.setChecked(False)
    # Then the base must revert to 32:
    assert form.ui.combobox_base.currentText() == "32"


def test_update():
    """Update an existing password."""
    # Given:
    nick, user, host, iteration, hint = "nick", "user", "host.com", 3, "hint"
    orig_password = Password(nick, user, host, iteration=iteration, hint=hint)
    new_nick, new_user = "new_nick", "new_user"
    form = EditController()
    form.start()
    form.populate_form_from_password(orig_password)
    # Skip the "Are you sure?" messagebox:
    form.ui.edit_buttons.accepted.disconnect(form.confirm_accept)
    form.ui.edit_buttons.accepted.connect(form.accept)
    # When we update the original password:
    form.ui.lineedit_nickname.setText(new_nick)
    form.ui.lineedit_username.setText(new_user)
    ok_button = form.ui.edit_buttons.button(form.ui.edit_buttons.Ok)
    QTest.mouseClick(ok_button, Qt.LeftButton)
    password = form.create_password_from_form()
    # Then we get those updates back:
    assert form.dirty_flag
    assert form.update_flag
    assert form.result() == 1
    assert password == Password(new_nick, new_user, host, iteration=iteration, hint=hint)
