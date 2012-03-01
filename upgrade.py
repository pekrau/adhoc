" Upgrade to use WhoYou for accounts and teams."

import json
import sqlite3
import os.path

from adhoc import configuration
import whoyou.database


def add_teams(cnx, doit=False):
    "Add the teams from Adhoc to WhoYou."
    teams = set()
    cursor = cnx.cursor()
    cursor.execute('SELECT teams FROM account')
    for row in cursor:
        for item in row[0].split():
            teams.add(item)
    print 'Adhoc teams:', teams
    db = whoyou.database.Database()
    db.open()
    current = dict([(t.name, t) for t in db.get_teams()])
    print 'WhoYou teams:', current.keys()
    for team in teams:
        if team in current: continue
        if doit:
            print 'adding', team
            db.create_team(team)
    db.close()

def add_accounts(cnx, doit=False):
    "Add the accounts from Adhoc to WhoYou."
    accounts = dict()
    cursor = cnx.cursor()
    cursor.execute('SELECT name, description, password, email, teams,'
                   ' max_tasks, preferences FROM account')
    for row in cursor:
        accounts[row[0]] = dict(description=row[1],
                                password=row[2],
                                email=row[3],
                                teams=row[4].split(),
                                max_tasks=int(row[5]),
                                preferences=json.loads(row[6] or '{}'))
    print 'Adhoc accounts:', accounts.keys()
    db = whoyou.database.Database()
    db.open()
    current = dict([(t.name, t) for t in db.get_accounts()])
    print 'WhoYou accounts:', current.keys()
    for name, data in accounts.items():
        if name in current: continue
        if doit:
            print 'adding', name
            account = db.create_account(name, description=data['description'])
            account.email = data['email']
            account._hexdigest = data['password']
            account.properties = dict(Adhoc=dict(preferences=data['preferences'],
                                                 quotas=dict(ntasks=data['max_tasks'])))
            account.save()
            account.set_teams(data['teams'])
    db.close()


def modify_database(cnx, doit=False):
    try:
        cursor = cnx.cursor()
        cursor.execute('SELECT id, name FROM account')
    except sqlite3.OperationalError:
        print 'database already modified'
        return
    accounts = dict(cursor.fetchall())
    if doit:
        cursor.execute('CREATE TABLE task_new'
                       '(id INTEGER PRIMARY KEY,'
                       ' iui TEXT UNIQUE NOT NULL,'
                       ' tool TEXT NOT NULL,'
                       ' title TEXT,'
                       ' status TEXT NOT NULL,'
                       ' pid INTEGER,'
                       ' size INTEGER NOT NULL,'
                       ' cpu_time REAL,'
                       ' account TEXT NOT NULL,'
                       ' modified TEXT NOT NULL)')
    cursor.execute('SELECT id,iui,tool,title,status,pid,size,modified,'
                   ' account FROM task')
    rows = []
    for row in cursor:
        row = list(row)
        row[6] = row[6] or 0            # Size changed to NOT NULL
        row[8] = accounts[row[8]]       # Account changed to string
        rows.append(row)
    if doit:
        for row in rows:
            cursor.execute('INSERT INTO task_new (id,iui,tool,title,'
                           ' status,pid,size,modified,account)'
                           ' VALUES(?,?,?,?,?,?,?,?,?)', row)
        cursor.execute('DROP TABLE account')
        cursor.execute('DROP TABLE task')
        cursor.execute('ALTER TABLE task_new RENAME TO task')
        cursor.execute('CREATE INDEX task_account_index ON task(account)')
        cursor.execute('VACUUM')

def move_cpu_time(cnx, doit=False):
    "Copy over cpu_time entry from task data file to master table."
    cursor = cnx.cursor()
    cursor.execute('SELECT iui FROM task')
    for iui in [row[0] for row in cursor]:
        infile = open(os.path.join(configuration.TASK_DIR, iui))
        data = json.loads(infile.read())
        infile.close()
        try:
            cpu_time = float(data['cpu_time'])
        except (KeyError, ValueError):
            pass
        else:
            if doit:
                cursor.execute('UPDATE task SET cpu_time=? WHERE iui=?',
                               (cpu_time, iui))
    if doit:
        cnx.commit()


if __name__ == '__main__':
    import sys
    print 'Adhoc data directory:', configuration.DATA_DIR
    print 'WhoYou database:', whoyou.database.configuration.MASTER_DB_FILE
    answer = raw_input('OK? ')
    if not answer or answer.upper()[0] == 'N': sys.exit()
    cnx = sqlite3.connect(configuration.MASTER_DB_FILE)
    cnx.text_factory = str
    add_teams(cnx, doit=True)
    add_accounts(cnx, doit=True)
    modify_database(cnx, doit=True)
    move_cpu_time(cnx, doit=True)
