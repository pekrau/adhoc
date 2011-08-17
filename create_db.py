""" Adhoc web resource.

Create the database from scratch, and the 'admin' account.
"""

import sys
import os.path
import sqlite3

from adhoc import configuration


def create_db(admin_password):
    assert not os.path.exists(configuration.ADHOC_FILE)
    cnx = sqlite3.connect(configuration.ADHOC_FILE)
    cursor = cnx.cursor()
    cursor.execute('CREATE TABLE account'
                   '(id INTEGER PRIMARY KEY,'
                   ' name TEXT UNIQUE NOT NULL,'
                   ' password TEXT,'
                   ' teams TEXT,'
                   ' email TEXT,'
                   ' preferences TEXT,'
                   ' description TEXT)')
    cursor.execute('INSERT INTO account(name,password,teams,email,description)'
                   ' VALUES(?, ?, ?, ?, ?)',
                   ('admin',
                    configuration.get_password_hexdigest(admin_password),
                    'admin',
                    None,
                    'Site administrator.'))
    cursor.execute('CREATE TABLE task'
                   '(id INTEGER PRIMARY KEY,'
                   ' iui TEXT UNIQUE NOT NULL,'
                   ' tool TEXT NOT NULL,'
                   ' title TEXT,'
                   ' status TEXT NOT NULL,'
                   ' pid INTEGER,'
                   ' size INTEGER,'
                   ' modified TEXT NOT NULL,'
                   ' account INTEGER REFERENCES account(id) ON DELETE RESTRICT)')
    cnx.commit()
    cnx.close()

if __name__ == '__main__':
    import getpass
    if os.path.exists(configuration.ADHOC_FILE):
        print 'Error: database already exists!'
        sys.exit(1)
    password = getpass.getpass("Give the password for the 'admin' account > ")
    create_db(password)
    print 'Database created.'
