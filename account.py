""" Adhoc web resource.

Account web resources.
"""

from .webresource import *


def get_tasks_stats(cnx, id):
    "Return number of tasks and total tasks size."
    cursor = cnx.cursor()
    cursor.execute('SELECT COUNT(*) FROM task WHERE account=?', (id,))
    number = cursor.fetchone()[0]
    cursor.execute('SELECT SUM(size) FROM task WHERE account=?', (id,))
    size = cursor.fetchone()[0] or 0
    return number, size


class Accounts(WebResource):
    "Handle accounts."

    def GET(self, request, response):
        self.check_admin()
        html = HtmlRepresentation(self, 'Accounts')
        rows = [TR(TH('Name'),
                   TH('Teams'),
                   TH('Email'),
                   TH('# tasks'),
                   TH('Total task size'))]
        cursor = self.execute('SELECT id,name,teams,email'
                              ' FROM account ORDER BY name')
        for record in cursor:
            id, name, teams, email = record
            number, size = get_tasks_stats(self.cnx, id)
            rows.append(TR(TD(A(name,
                                href=configuration.get_url('account', name))),
                           TD(teams or NONE),
                           TD(email or NONE),
                           TD(A(str(number),
                                href=configuration.get_url('tasks', name)),
                              klass='number'),
                           TD(str(size), klass='number')))
        html.append(TABLE(klass='list', *rows))
        html.add_operation('Create account', 'account')
        html.write(response)


class Account(WebResource):
    "Display account data."

    def prepare(self, request, response):
        super(Account, self).prepare(request, response)
        self.name = request.path_named_values['name']
        cursor = self.execute('SELECT id,password,teams,email,description'
                              ' FROM account WHERE name=?', self.name)
        record = cursor.fetchone()
        if not record:
            raise HTTP_NOT_FOUND
        self.account_id, self.password, teams, self.email, self.description = \
            record
        self.teams = set(teams.split())

    def GET(self, request, response):
        self.check_read()
        html = HtmlRepresentation(self, "Account %s" % self.name)
        rows = []
        rows.append(TR(TH('Teams'),
                       TD(' '.join(self.teams) or NONE)))
        if self.email:
            email = A(self.email, href="mailto:%s" % self.email)
        else:
            email = NONE
        rows.append(TR(TH('Email'),
                       TD(email)))
        if self.description:
            description = markdown.markdown(self.description,
                                            output_format='html4')
        else:
            description = NONE
        rows.append(TR(TH('Description'),
                       TD(description)))
        number, size = get_tasks_stats(self.cnx, self.account_id)
        rows.append(TR(TH('# tasks'),
                       TD(A(str(number),
                            href=configuration.get_url('tasks', self.name)))))
        rows.append(TR(TH('Total tasks size'),
                       TD(str(size))))
        html.append(TABLE(klass='input', *rows))
        html.add_operation('Edit account', 'account', self.name, 'edit')
        html.write(response)

    def check_read(self):
        "Raise HTTP FORBIDDEN if user does not have read privilege."
        if self.is_admin(): return
        if self.user['name'] != self.name: raise HTTP_FORBIDDEN


class AccountEdit(Account):
    "Edit account data."

    def check_write(self):
        "Raise HTTP FORBIDDEN if user does not have write privilege."
        if self.is_admin(): return
        if self.user['name'] != self.name: raise HTTP_FORBIDDEN

    def GET(self, request, response):
        self.check_read()
        html = HtmlRepresentation(self, "Edit account %s" % self.name)
        url = configuration.get_url('account', self.name, 'edit')
        rows = []
        if not self.is_admin():
            rows.append(TR(TH('Current password'),
                           TD(REQUIRED),
                           TD(INPUT(type='password', name='current_password'))))
        rows.append(TR(TH('New password'),
                       TD(REQUIRED),
                       TD(INPUT(type='password', name='new_password'))))
        rows.append(TR(TH('Confirm password'),
                       TD(REQUIRED),
                       TD(INPUT(type='password', name='confirm_password'))))
        if self.is_admin():
            rows.append(TR(TH('Teams'),
                           TD(),
                           TD(*[DIV(INPUT(type='checkbox', name='team', value=t,
                                          checked=(t in self.teams)),
                                    t)
                                for t in sorted(configuration.TEAMS)])))
        else:
            rows.append(TR(TH('Teams'),
                           TD(),
                           TD(I('[only admin may change your teams]'))))
        rows.append(TR(TH('Email'),
                       TD(),
                       TD(INPUT(type='text', size=40,
                                name='email', value=self.email or ''))))
        rows.append(TR(TH('Description'),
                       TD(),
                       TD(TEXTAREA(self.description or '',
                                   cols=60, rows=6, name='description'))))
        html.append(FORM(TABLE(klass='input', *rows),
                         P(INPUT(type='submit', value='Update')),
                         method='POST',
                         action=url))
        html.append(P(FORM(INPUT(type='submit', value='Cancel'),
                           method='GET',
                           action=configuration.get_url('account', self.name))))
        html.write(response)

    def POST(self, request, response):
        self.check_write()
        if not self.is_admin():
            current_password = self.get_cgi_value('current_password')
            if current_password:
                current_password = configuration.get_password_hexdigest(current_password)
                if self.password != current_password:
                    raise HTTP_BAD_REQUEST("invalid 'current_password' value")
        new_password = self.get_cgi_value('new_password')
        if new_password:
            confirm_password = self.get_cgi_value('confirm_password', required=True)
            if new_password != confirm_password:
                raise HTTP_BAD_REQUEST("invalid 'confirm_password' value")
            self.execute('UPDATE account SET password=? WHERE name=?',
                         configuration.get_password_hexdigest(new_password),
                         self.name)
        if self.is_admin():
            teams = ' '.join(request.cgi_fields.getlist('team'))
        else:
            teams = ' '.join(self.teams)
        email = self.get_cgi_value('email')
        description = self.get_cgi_value('description', cleanup=True)
        self.execute('UPDATE account SET teams=?, email=?, description=?'
                     ' WHERE name=?', teams, email, description, self.name)
        self.commit()
        url = configuration.get_url('account', self.name)
        raise HTTP_SEE_OTHER(Location=url)


class AccountCreate(WebResource):
    "Handle creation of an account."

    def GET(self, request, response):
        self.check_admin()
        html = HtmlRepresentation(self, 'Create account')
        rows = [TR(TH('Name'),
                   TD(REQUIRED),
                   TD(INPUT(type='text', name='name')),
                   TD(I('Must be unique'))),
                TR(TH('Password'),
                   TD(REQUIRED),
                   TD(INPUT(type='password', name='password')),
                   TD()),
                TR(TH('Confirm password'),
                   TD(REQUIRED),
                   TD(INPUT(type='password', name='confirm_password')),
                   TD()),
                TR(TH('Teams'),
                   TD(*[DIV(INPUT(type='checkbox', name='team', value=team),
                            team)
                        for team in sorted(configuration.TEAMS)])),
                TR(TH('Email'),
                   TD(),
                   TD(INPUT(type='text', name='email')),
                   TD()),
                TR(TH('Description'),
                   TD(),
                   TD(TEXTAREA(cols=60, rows=6, name='description')),
                   TD())]
        html.append(FORM(TABLE(klass='input', *rows),
                         P(INPUT(type='submit', value='Create')),
                         method='POST',
                         action=configuration.get_url('account')))
        html.append(FORM(P(INPUT(type='submit', value='Cancel')),
                         method='GET',
                         action=configuration.get_url('accounts')))
        html.write(response)

    def POST(self, request, response):
        self.check_admin()
        name = self.get_cgi_value('name', required=True)
        cursor = self.execute('SELECT COUNT(*) FROM account WHERE name=?', name)
        if cursor.fetchone()[0] != 0:
            raise HTTP_BAD_REQUEST("account '%s' already exists" % name)
        password = self.get_cgi_value('password', required=True)
        confirm_password = self.get_cgi_value('confirm_password', required=True)
        if password != confirm_password:
            raise HTTP_BAD_REQUEST('password and confirm password not the same')
        teams = ' '.join(request.cgi_fields.getlist('team'))
        email = self.get_cgi_value('email')
        description = self.get_cgi_value('description', cleanup=True)
        self.execute('INSERT INTO account(name,password,teams,email,description)'
                     ' VALUES(?,?,?,?,?)',
                     name,
                     configuration.get_password_hexdigest(password),
                     teams,
                     email,
                     description)
        self.commit()
        raise HTTP_SEE_OTHER(Location=configuration.get_url('account', name))
