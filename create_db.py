""" Adhoc web resource.

Create the database from scratch, and the 'admin' account.
"""

import sys
import os.path
import getpass
import sqlite3

from adhoc import configuration


def create_db(admin_password):
    assert not os.path.exists(configuration.MASTER_DBFILE)
    cnx = sqlite3.connect(configuration.MASTER_DBFILE)
    cursor = cnx.cursor()
    cursor.execute('CREATE TABLE account'
                   '(id INTEGER PRIMARY KEY,'
                   ' name TEXT UNIQUE NOT NULL,'
                   ' password TEXT,'
                   ' teams TEXT,'
                   ' max_tasks INTEGER,'
                   ' email TEXT,'
                   ' preferences TEXT,'
                   ' description TEXT)')
    cursor.execute('CREATE TABLE task'
                   '(id INTEGER PRIMARY KEY,'
                   ' iui TEXT UNIQUE NOT NULL,'
                   ' href TEXT UNIQUE NOT NULL,'
                   ' tool TEXT NOT NULL,'
                   ' title TEXT,'
                   ' status TEXT NOT NULL,'
                   ' pid INTEGER,'
                   ' size INTEGER,'
                   ' modified TEXT NOT NULL,'
                   ' account INTEGER REFERENCES account(id) ON DELETE RESTRICT)')
    create_account(cursor, 'admin', admin_password, 'admin',
                   -1, None, 'Site administrator')
    create_account(cursor, 'anonymous', '', '',
                   4, None, 'Anonymous user.')
    try:
        from adhoc.tests import configuration as test_conf
        create_account(cursor, test_conf['ACCOUNT'], test_conf['PASSWORD'], '',
                       4, None, 'Test account.')
    except (ImportError, KeyError):
        pass
    cnx.commit()
    cnx.close()

def create_account(cursor, name, password, teams, max_tasks, email,description):
    if password:
        password = configuration.get_password_hexdigest(password)
    cursor.execute('INSERT INTO account(name,password,teams,'
                   ' max_tasks,email,description)'
                   ' VALUES(?,?,?,?,?,?)',
                   (name,
                    password,
                    teams,
                    max_tasks,
                    email,
                    description))
    

if __name__ == '__main__':
    if os.path.exists(configuration.MASTER_DBFILE):
        print 'Error: database already exists!'
        sys.exit(1)
    password = getpass.getpass("Give the password for the 'admin' account > ")
    create_db(password)
    print 'Database created.'
