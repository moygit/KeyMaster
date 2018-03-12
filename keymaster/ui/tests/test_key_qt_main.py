#!/usr/bin/env python3

"""Basic usage unit-tests for the main form."""

import sys

import nose

from PyQt5 import QtWidgets
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from keymaster.key_password import Password
from keymaster.key_password import PasswordDB
from keymaster.ui.key_qt_main import MainController

APP = QtWidgets.QApplication(sys.argv)

NICK1, USER1, HOST1, SPCHAR1, BASE1, ITER1, HINT1, START1, FINISH1 = \
        "nick1", "user1", "host1", True, 64, 3, "hint1", 10, 30
NICK2, USER2, HOST2, SPCHAR2, BASE2, ITER2, HINT2, START2, FINISH2 = \
        "nick2", "user2", "host2", False, 32, 4, "hint2", 20, 30


def _get_test_db():
    """Get a test (in-memory) database and the corresponding dictionary."""
    pass_db = PasswordDB(":memory:", True)
    pass1 = Password(NICK1, USER1, HOST1, SPCHAR1, BASE1, ITER1, HINT1, START1, FINISH1)
    pass2 = Password(NICK2, USER2, HOST2, SPCHAR2, BASE2, ITER2, HINT2, START2, FINISH2)
    pass_db.create_new_password(pass1)
    pass_db.create_new_password(pass2)
    return pass_db, {NICK1: pass1, NICK2: pass2}


def test_do_nothing():
    """Just create the form and reject it (like pressing escape)."""
    # Given:
    form = MainController(APP)
    form.start(*_get_test_db())
    # When we do nothing:
    form.reject()
    # Then check defaults and form returns 1 because we ok'ed:
    assert len(form.passwords_dic) == 2
    assert str(form.pass_db) == 'PasswordDB(":memory:")'

def test_hint():
    """Use the test db and verify the hint for one password."""
    # Given:
    form = MainController(APP)
    form.start(*_get_test_db())
    # When we get the hint:
    form.ui.combobox_password_nicknames.setCurrentText(NICK1)
    QTest.mouseClick(form.ui.button_hint, Qt.LeftButton)
    # Then it matches what we created:
    assert form.ui.label_resp_body.text() == HINT1


def test_get():
    """Use the test db and verify the real password for one password."""
    # Given:
    form = MainController(APP)
    form.start(*_get_test_db())
    # When we get the password (it's ok to leave the proto blank):
    form.ui.combobox_password_nicknames.setCurrentText(NICK2)
    QTest.mouseClick(form.ui.button_get, Qt.LeftButton)
    # Then it matches what we created:
    assert len(form.ui.label_resp_body.text()) == FINISH2 + 1 - START2


def test_delete():
    """Use the test db and verify deleting one password."""
    # Given:
    form = MainController(APP)
    form.start(*_get_test_db())
    form.ui.button_delete.clicked.disconnect(form.delete_password)
    form.ui.button_delete.clicked.connect(lambda: form.delete_password(confirmed=True))
    # When we get the password (it's ok to leave the proto blank):
    form.ui.combobox_password_nicknames.setCurrentText(NICK2)
    QTest.mouseClick(form.ui.button_delete, Qt.LeftButton)
    # Then it matches what we created:
    assert len(form.passwords_dic) == 1
    assert NICK2 not in form.passwords_dic
    assert NICK1 in form.passwords_dic


@nose.tools.nottest # figure out how to handle the edit-form
def test_create():
    """Create a new password."""
    # Given:
    nick, user, host, iteration, hint = "nick", "user", "host.com", 3, "hint"
    form = MainController(APP)
    form.start(PasswordDB(":memory:", True), {})
    QTest.mouseClick(form.ui.button_new, Qt.LeftButton)
    # Now populate the edit form:
    form.edit_form.ui.lineedit_nickname.setText(nick)
    form.edit_form.ui.lineedit_username.setText(user)
    form.edit_form.ui.lineedit_hostname.setText(host)
    form.edit_form.ui.spinbox_iteration.setValue(iteration)
    form.edit_form.ui.lineedit_hint.setText(hint)
    ok_button = form.edit_form.ui.edit_buttons.button(form.edit_form.ui.edit_buttons.Ok)
    QTest.mouseClick(ok_button, Qt.LeftButton)
    # Then we get that new pw back:
    password = form.passwords_dic[nick]
    assert password == Password(nick, user, host, iteration=iteration, hint=hint)
