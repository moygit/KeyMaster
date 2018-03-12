#!/usr/bin/python3

"""Tests:
- Command-line arguments
- Basic tests for subcommands
- A few tests for data with errors
"""

from io import StringIO
import sys
from nose.tools import raises

import keymaster.key_password as pw
import keymaster.cli.key_cli as cli


TEST_CREATE_INPUT = "nick\nuser\nhost\ny\n\n\nhint\n\n20\n"
# "abcd" in the input below should be a number; the error is fixed by the blank right after it:
TEST_CREATE_INPUT_WITH_ERR = "nick\nuser\nhost\ny\nabcd\n\n\nhint\n\n20\n"
TEST2_CREATE_INPUT = "nick2\nuser2\nhost2\ny\n\n\nhint2\n5\n15\n"
TEST_ENTER_PROTO_PW = "pass\nqass\npass\npass\n"    # Mismatch first time, then match


def test_empty_commands():
    """Test commands without nick supplied on the command-line."""
    for command, func_desc in cli.COMMANDS_MAP:
        # given:
        cmd_line = [command]
        # when:
        args = cli.parse_args(cmd_line)
        # then:
        assert args.nickname is None
        assert args.func == func_desc["func"]


def test_nonempty_commands():
    """Test commands with nick supplied on the command-line."""
    for command, func_desc in cli.COMMANDS_MAP:
        # given:
        cmd_line = [command, "abcd"]
        # when:
        args = cli.parse_args(cmd_line)
        # then:
        assert args.nickname == "abcd"
        assert args.func == func_desc["func"]


@raises(SystemExit)     # then
def test_call_with_bad_command():
    """Non-existent subcommand ("other") should raise an error."""
    save_stderr, sys.stderr = sys.stderr, sys.stdout
    # given:
    cmd_line = ["other"]
    # when:
    cli.parse_args(cmd_line)
    sys.stderr = save_stderr


def _create_dummy(input_str):
    """Create a dummy password for testing."""
    pdic, pdb = {}, pw.PasswordDB(":memory:", True)
    save_stdin, sys.stdin = sys.stdin, StringIO(input_str)
    expected_nick = "nick"
    assert cli.create_pass(None, pdb, pdic) == expected_nick
    assert expected_nick in pdic
    assert pdb.get_list_of_nicks() == [expected_nick]
    sys.stdin = save_stdin
    return pdic, pdb


def test_create():
    """Test a basic create."""
    # given/when:
    pdic, _ = _create_dummy(TEST_CREATE_INPUT)
    # then:
    expected_nick = "nick"
    assert pdic[expected_nick].special_char
    assert pdic[expected_nick].base == 32
    assert pdic[expected_nick].iteration == 1
    assert pdic[expected_nick].start == 0
    assert pdic[expected_nick].finish == 20


def test_create_with_num_error():
    """Test creation with a numerical error in the input."""
    # given/when:
    pdic, _ = _create_dummy(TEST_CREATE_INPUT_WITH_ERR)
    # then:
    expected_nick = "nick"
    assert pdic[expected_nick].special_char
    assert pdic[expected_nick].base == 32
    assert pdic[expected_nick].iteration == 1
    assert pdic[expected_nick].start == 0
    assert pdic[expected_nick].finish == 20


def test_delete():
    """Create, then delete."""
    # First create:
    pdic, pdb = _create_dummy(TEST_CREATE_INPUT)
    # And now delete:
    # given/when:
    nick = "nick"
    cli.delete_pass(nick, pdb, pdic)
    # then:
    assert nick not in pdic
    assert pdb.get_list_of_nicks() == []


def test_hint():
    """Create, then check hint."""
    # First create:
    pdic, pdb = _create_dummy(TEST_CREATE_INPUT)
    # And now get the hint:
    # given:
    nick = "nick"
    expected_hint = "Hint: hint"
    # when:
    save_stdout, sys.stdout = sys.stdout, StringIO()
    cli.hint_pass(nick, pdb, pdic)
    output, sys.stdout = sys.stdout.getvalue(), save_stdout
    # then:
    assert output.strip() == expected_hint


def test_update():
    """Create, then update."""
    # First create:
    pdic, pdb = _create_dummy(TEST_CREATE_INPUT)
    old_nick = "nick"
    # And now update:
    # given:
    save_stdin, sys.stdin = sys.stdin, StringIO(TEST2_CREATE_INPUT)
    new_nick = "nick2"
    # when:
    assert cli.update_pass("nick", pdb, pdic) == new_nick
    sys.stdin = save_stdin
    # then:
    assert old_nick not in pdic
    assert new_nick in pdic
    assert pdb.get_list_of_nicks() == [new_nick]


def test_get():
    """Can't test get because of how getpass handles I/O.
    Do it manually.
    """
    assert True
