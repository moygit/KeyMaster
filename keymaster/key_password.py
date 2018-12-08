#!/usr/bin/env python3

"""KeyMaster internals (Password and PasswordDB classes)
"""

import base64
from hashlib import sha512
import os
from pathlib import Path
import sqlite3
from xdg import XDG_CONFIG_HOME


DEFAULT_DB_PATH = Path(XDG_CONFIG_HOME, "keymaster", ".passwords.db")

_DROP_PASSWORDS_TABLE_SCHEMA = """drop table if exists passwords;"""
_CREATE_PASSWORDS_TABLE_SCHEMA = """
create table passwords
(
    nickname text,
    username text,
    hostname text,
    special_char boolean,
    base integer,
    iteration integer,
    hint text,
    start integer,
    finish integer
);
"""

_SQL_INS_PASS = "insert into passwords values(?,?,?,?,?,?,?,?,?);"
_SQL_GET_NICK = "select nickname from passwords;"
_SQL_GET_PASS_BY_NICK = "select * from passwords where nickname = ?;"
_SQL_GET_PASS = "select * from passwords;"
_SQL_DEL_PASS = "delete from passwords where nickname = ?;"

_DB_DOES_NOT_EXIST = "DB file {} does not exist but you asked me not to create it"

_CHR_ENCODING = "utf-8"

# public for tests
REPR = "Password({nickname}, {username}, {hostname}, {special_char}, {base}, {iteration}, {hint}, {start}, {finish})"


class Password:
    """Keep all info about a single password together."""
    translator = str.maketrans("acers", "@(*^$")

    def __init__(self, nickname="", username="", hostname="", special_char=False,
                 base=32, iteration=1, hint="", start=0, finish=15):
        self.nickname = str(nickname)
        self.username = str(username)
        self.hostname = str(hostname)
        self.special_char = special_char
        self.base = base
        self.iteration = iteration
        self.hint = str(hint)
        self.start = start
        self.finish = finish

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return REPR.format(**self.__dict__)

    def calculate_password(self, user_proto_pw):
        """Do the actual password calculation."""
        # add username @ hostname iteration, and then hash:
        proto_pw = user_proto_pw + self.username + '@' + self.hostname + str(self.iteration)
        if self.base == 32:
            encode_fn = base64.b32encode
        if self.base == 64:
            encode_fn = base64.b64encode
        password_str = encode_fn(sha512(str(proto_pw).encode(_CHR_ENCODING)).digest())
        password_str = password_str[self.start:self.finish+1].lower()
        password_str = password_str.decode(_CHR_ENCODING)
        # change a few letters:
        password_str = password_str.replace('b', 'B', 1).replace('d', 'D', 1).replace('z', 'Z', 1)
        if self.special_char:
            password_str = password_str.translate(Password.translator)
        return password_str


class PasswordDB:
    """Encapsulate all our CRUD operations."""

    # We do basic error-checking when we initialize: return True(or
    #     list of nicknames) if we're able go get a db-handle,
    #     False if not.
    # From there on(since we have minimal human input) errors can
    #     only be catastrophic and would be meaningless to users.
    # Note: if the file exists but doesn't contain the required
    #     database we get an error.
    def __init__(self, db_name, create_new_db):
        self.db_name = db_name
        self.conn = sqlite3.connect(str(self.db_name))  # note: this creates the file if it doesn't exist
        self.cur = self.conn.cursor()
        if create_new_db:
            self.cur.execute(_DROP_PASSWORDS_TABLE_SCHEMA)
            self.cur.execute(_CREATE_PASSWORDS_TABLE_SCHEMA)
            self.conn.commit()

    @staticmethod
    def get_data(ask_to_create_new_func, error_getting_db_func, db_name=DEFAULT_DB_PATH):
        """Open the database and get passwords dictionary."""
        # Try to open the database:
        root = os.path.dirname(db_name)
        if os.path.exists(db_name):
            pass_db = PasswordDB(db_name, create_new_db=False)
        else:
            create_new_db = ask_to_create_new_func()
            if create_new_db:
                if not os.path.exists(root):
                    os.makedirs(root)
                pass_db = PasswordDB(db_name, create_new_db=True)
            else:
                return None, None
        if pass_db is None:
            error_getting_db_func()
            return None, None
        passwords_dic = pass_db.get_all_password_objects()
        return pass_db, passwords_dic

    def __repr__(self):
        return 'PasswordDB("%s")' % self.db_name

    def get_list_of_nicks(self):
        """Get list of all nicknames in password database."""
        self.cur.execute(_SQL_GET_NICK)
        return sorted([pw[0] for pw in self.cur.fetchall()])

    def get_password_for_nick(self, nickname):
        """Get password for a particular nick."""
        self.cur.execute(_SQL_GET_PASS_BY_NICK, (nickname,))    # nickname could be untrusted user input
        return Password(*(self.cur.fetchall()[0]))

    def get_all_password_objects(self):
        """Get all passwords in password database."""
        self.cur.execute(_SQL_GET_PASS)
        return {row[0]: Password(*row) for row in self.cur.fetchall()}

    def create_new_password(self, pw_obj):
        """Create a new password in the password database."""
        self._run_create(pw_obj)
        self.conn.commit()

    def _run_create(self, pw_obj):
        """Run the create command against the database."""
        self.cur.execute(_SQL_INS_PASS,                         # Fields could be untrusted user input
                         (pw_obj.nickname, pw_obj.username, pw_obj.hostname,
                          pw_obj.special_char, pw_obj.base, pw_obj.iteration,
                          pw_obj.hint, pw_obj.start, pw_obj.finish))

    def update_old_password(self, orig_nick, pw_obj):
        """Update an existing password in the password database."""
        # We delete and then create (instead of updating) in case nickname itself changes.
        self._run_delete(orig_nick)
        self._run_create(pw_obj)
        self.conn.commit()

    def delete_password(self, nickname_or_pw_obj):
        """Delete an existing password from the password database."""
        if isinstance(nickname_or_pw_obj, Password):
            nickname = nickname_or_pw_obj.nickname
        else:
            nickname = nickname_or_pw_obj
        self._run_delete(nickname)
        self.conn.commit()

    def _run_delete(self, nickname):
        """Delete a password by nickname."""
        self.cur.execute(_SQL_DEL_PASS, (nickname,))            # nickname could be untrusted user input

    def close_db(self):
        """Close database connection."""
        self.conn.commit()
        self.conn.close()
