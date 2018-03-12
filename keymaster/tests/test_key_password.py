#!/usr/bin/env python3
# pylint: disable=missing-docstring

"""Tests included:
- Password usage, 32-bit, no special chars
- Password usage, 64-bit, with special chars
- Password equality
- PasswordDB usage, basic functions
"""

import nose
import keymaster.key_password as pw


_NICK = "nick"


def test_basic_usage_no_sp_chars():
    # Given/when:
    password = _get_basic_password()
    expected_password = "5wjDnwdyj4uxZd6g"
    # Then:
    assert str(password) == pw.REPR.format(**password.__dict__)
    assert password.calculate_password("") == expected_password


def test_basic_usage_with_sp_chars():
    # Given/when:
    special, iteration_num = True, 2
    password = _get_basic_password(special, iteration_num)
    expected_password = "$ifZ6kv@p9xmyf(1"
    # Then:
    assert str(password) == pw.REPR.format(**password.__dict__)
    assert password.calculate_password("") == expected_password


def test_pw_equality():
    # Given/when:
    pw1 = _get_basic_password()
    pw2 = _get_basic_password()
    special, iteration_num = True, 2
    pw3 = _get_basic_password(special, iteration_num)
    # Then:
    assert pw1 == pw2
    assert not pw1 != pw2   # pylint: disable=unneeded-not
    assert pw1 != pw3


def test_basic_pwdb_usage():
    # Empty DB:
    pdb = pw.PasswordDB(":memory:", True)
    assert str(pdb) == 'PasswordDB(":memory:")'
    assert pdb.get_list_of_nicks() == []

    # Add one entry and test single-pass methods:
    password = _get_basic_password(True, 2)
    pdb.create_new_password(password)
    assert pdb.get_password_for_nick(_NICK) == password

    # Test "all" methods:
    all_passwords = pdb.get_all_password_objects()
    assert len(all_passwords) == 1
    assert all_passwords[_NICK] == password
    assert pdb.get_list_of_nicks() == [_NICK]

    # Test delete:
    pdb.delete_password(_NICK)
    assert pdb.get_list_of_nicks() == []


def _get_basic_password(special=False, iteration_num=1):
    """Return a basic Password object based on whether to use special
    chars and the specified iteration number.
    """
    user, host, hint, start, finish = \
        "user", "host", "hint", 0, 15
    base = 64 if special else 32
    return pw.Password(_NICK, user, host, special, base, iteration_num, hint, start, finish)


if __name__ == '__main__':
    nose.main()
