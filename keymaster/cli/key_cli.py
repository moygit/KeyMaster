#!/usr/bin/python3

"""Handle the command-line interface to keymaster.

Example
----
$ keymaster get nick
Enter proto-password (won't be displayed): *********
Again, please (to avoid mistakeS): *********
Password: password

$ keymaster get
Select which password to get from the following list:
 1) bank: bank_username@bank.com
 2) fbi: fbi_username@login.fbi.gov
 3) whitehouse: president@whitehouse.gov
Choose identity: 3
Enter proto-password (won't be displayed): *********
Again, please (to avoid mistakeS): *********
Password: password

"""


import argparse
from collections import OrderedDict
import getpass
import sys

from keymaster.key_password import DEFAULT_DB_PATH
from keymaster.key_password import Password
from keymaster.key_password import PasswordDB


_MSG_NO_PASS_DB = "Password database doesn't already exist."
_MSG_CREATE_NEW = "Create a new one? (y/[n])"
_MSG_ERROR_OPENING_DB = "Error opening passwords db. Exiting."
_MSG_NICK_IN_USE = "Nickname already in use. Please try again."
_MSG_NICK_NOT_FOUND = "Nickname {} not found."
_MSG_SELECT_NICK = "Choose identity: "

_MSG_ENTER_PROTO_PW_1 = "Proto-password (won't be displayed): "
_MSG_ENTER_PROTO_PW_2 = "Again, please (to avoid mistakes): "
_MSG_PROTO_PW_MISMATCH = "The two proto-passwords don't match.  Please try again."


def main():
    """Do it!"""
    args = parse_args(sys.argv[1:])
    pass_db, passwords_dic = _get_data(args.db_path)
    if pass_db is None:
        sys.exit(1)
    args.func(args.nickname, pass_db, passwords_dic)


def _get_data(db_path):
    """Create communications methods for the back-end get_data and call it."""
    def ask_to_create_new():
        """Is it okay to write a new db?"""
        print(_MSG_NO_PASS_DB)
        create_new = (input(_MSG_CREATE_NEW) + "n").lower()[0]
        return create_new == "y"
    def error_getting_db():
        """Couldn't get a handle to the database."""
        print(_MSG_ERROR_OPENING_DB, file=sys.stderr)
    return PasswordDB.get_data(ask_to_create_new, error_getting_db, db_path)


def create_pass(nick, pass_db, pass_dic):
    """Read in new password info and create and store the new object."""
    # get new password object:
    new_pass = _create_pass_get_new_pass(nick, pass_dic)
    # and write it:
    pass_dic[new_pass.nickname] = new_pass
    pass_db.create_new_password(new_pass)
    return new_pass.nickname


def _create_pass_get_new_pass(nick, pass_dic):
    """Read in new password info."""
    nick = _create_pass_get_nick(nick, pass_dic)
    # read in data:
    username = input("Username: ")
    hostname = input("Hostname: ")
    special_char = (input("special characters (y/[n]): ") + "n").lower()[0] == "y"      # "" defaults to "n"
    base = _read_default_int("Base ([32]/64): ", 32)
    iteration = _read_default_int("Iteration [1]: ", 1)
    hint = input("Hint: ")
    start_char = _read_default_int("Start char index (default: 0): ", 0)
    end_char = _read_default_int("End char index (default: 15): ", 15)
    # create new Password object:
    return Password(nick, username, hostname, special_char, base, iteration, hint, start_char, end_char)


def _create_pass_get_nick(nick, pass_dic):
    """If we already have a nickname use that, else read from input
    until we have one that's not in the password-dictionary already.
    """
    if nick is None:
        nick = input('Nickname: ')
    while nick in pass_dic:
        print(_MSG_NICK_IN_USE, file=sys.stderr)
        nick = input('Nickname: ')
    return nick


def _read_default_int(prompt, default):
    """Re-read input until the user either enters a number (which we return)
    or just hits enter (in which case we return the default).
    """
    num = None
    while num is None:
        user_input = input(prompt)
        if user_input == "":
            num = default
        else:
            try:
                num = int(user_input)
            except ValueError:
                pass
    return num


def update_pass(nick, pass_db, pass_dic):
    """Get info for new password, delete the old one, and then create the new one.
    We create a new one in order to allow changing the nickname (which we use as the key).
    """
    # get and display old password info:
    old_pw = _select_pass(nick, pass_db, pass_dic)
    print("About to update the following password object:")
    list_pass(old_pw.nickname, pass_db, pass_dic)
    # get new password object:
    print("Please enter new password information:")
    new_pass = _create_pass_get_new_pass(nick, pass_dic)
    # and only now delete the old one, and then write the new one:
    delete_pass(old_pw.nickname, pass_db, pass_dic)
    pass_dic[new_pass.nickname] = new_pass
    pass_db.create_new_password(new_pass)
    return new_pass.nickname


def get_pass(nick, pass_db, pass_dic):
    """Get the proto-password for this Password object from the user,
    and display the calculated password for this proto-password and Password.
    """
    def _get_proto_password():
        """Get proto-password from user."""
        proto_pw1 = getpass.getpass(_MSG_ENTER_PROTO_PW_1)
        proto_pw2 = getpass.getpass(_MSG_ENTER_PROTO_PW_2)
        return proto_pw1 if proto_pw1 == proto_pw2 else None

    pass_obj = _select_pass(nick, pass_db, pass_dic)

    # get a proto-password from the user:
    proto_pw = _get_proto_password()
    while proto_pw is None:
        print(_MSG_PROTO_PW_MISMATCH, file=sys.stderr)
        proto_pw = _get_proto_password()

    print("Password: " + pass_obj.calculate_password(proto_pw))


def hint_pass(nick, pass_db, pass_dic):
    """Print the hint for an existing password."""
    pass_obj = _select_pass(nick, pass_db, pass_dic)
    print("Hint: " + pass_obj.hint)


def delete_pass(nick, pass_db, pass_dic):
    """Delete an existing password from the db and the dict."""
    pass_obj = _select_pass(nick, pass_db, pass_dic)
    pass_db.delete_password(pass_obj)
    del pass_dic[pass_obj.nickname]


def list_pass(orig_nick, _, pass_dic):
    """List Password details either about the given nick (if non-None) or about all nicks."""
    if orig_nick is not None:
        if orig_nick in pass_dic:
            print(pass_dic[orig_nick])
        else:
            print(_MSG_NICK_NOT_FOUND.format(orig_nick), file=sys.stderr)
    else:
        for i, pass_pair in enumerate(sorted(pass_dic.items())):
            print(str(i+1) + ": " + str(pass_pair[1]))


def _select_pass(nick, pass_db, pass_dic):
    """If nick is non-empty and valid return the corresponding Password object.
    If empty or invalid then get a valid nick from the user.
    """
    if nick is not None:
        if nick in pass_dic:
            return pass_dic[nick]
        else:
            print(_MSG_NICK_NOT_FOUND.format(nick), file=sys.stderr)
    list_pass(None, pass_db, pass_dic)
    pos = None      # Note: pos is 0-based for Python, 1-based for user
    keys = sorted(list(pass_dic.keys()))
    while pos is None:
        pos = _read_default_int(_MSG_SELECT_NICK, None)
        if pos-1 not in range(len(keys)):
            pos = None
    return pass_dic[keys[pos-1]]


COMMANDS_MAP = [("create", {"func": create_pass, "desc": "create a new password"}),
                ("update", {"func": update_pass, "desc": "update an existing password"}),
                ("list", {"func": list_pass, "desc": "list details of an existing password (or all)"}),
                ("hint", {"func": hint_pass, "desc": "get the hint for an existing password"}),
                ("get", {"func": get_pass, "desc": "get an existing password"}),
                ("delete", {"func": delete_pass, "desc": "delete an existing password"})]


def parse_args(command_line):
    """Redirect each subcommand to the appropriate function."""
    parser = argparse.ArgumentParser(description="Manage passwords easily and securely")
    parser.add_argument("-d", "--db-path", default=DEFAULT_DB_PATH,
                        help="Alternate passwords-database path")
    subparsers = parser.add_subparsers(title="commands", description="valid subcommands", help="additional help")
    for cmd, cmd_data in OrderedDict(COMMANDS_MAP).items():
        subparser = subparsers.add_parser(cmd, description=cmd_data["desc"])
        subparser.add_argument("nickname", nargs="?", default=None)
        subparser.set_defaults(func=cmd_data["func"])
    parsed_args = parser.parse_args(command_line)
    if not parsed_args.func:
        parser.print_help()
        parser.exit()
    return parsed_args


if __name__ == "__main__":
    main()
