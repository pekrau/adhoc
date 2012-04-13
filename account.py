""" Adhoc: Simple web application for task execution.

Account: display usage and link to account details.
"""

from .method_mixin import *
from .representation import *


class AccountsHtmlRepresentation(HtmlRepresentation):
    "HTML to display list of accounts."

    def get_content(self):
        table = TABLE(TR(TH('Account'),
                         TH('# tasks'),
                         TH('Quota # tasks'),
                         TH('Size (bytes)'),
                         TH('CPU time (s)')),
                      klass='list')
        for account in self.data['accounts']:
            statistics = account['statistics']
            table.append(TR(TD(A(account['name'],
                                 href=account['href'])),
                            TD(A(statistics['count'],
                                 href=statistics['href']),
                               klass='integer'),
                            TD(account['quotas']['ntasks'], klass='integer'),
                            TD(statistics['size'], klass='integer'),
                            TD("%.1f" % statistics['cpu_time'],
                               klass='integer')))
        return table


class Accounts(MethodMixin, GET):
    "Display information on all accounts."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                AccountsHtmlRepresentation]

    def is_accessible(self):
        if self.is_login_admin(): return True
        return False

    def get_data_resource(self, request):
        get_url = request.application.get_url
        data = dict(title='Accounts')
        data['accounts'] = configuration.users.get_accounts()
        for account in data['accounts']:
            account['href'] = get_url('account', account['name'])
            account['statistics'] = self.db.get_statistics(account['name'])
            account['statistics']['href'] = get_url('tasks', account['name'])
            account['quotas'] = configuration.get_account_quotas(account)
        return data


class AccountHtmlRepresentation(HtmlRepresentation):
    "HTML to display account details."

    def get_content(self):
        account = self.data['account']
        statistics = account['statistics']
        quotas = account['quotas']
        stats = TABLE()
        stats.append(TR(TH('Current # tasks:'),
                        TD(A(statistics['count'],
                             href=statistics['href']),
                           klass='integer')))
        stats.append(TR(TH('Quota # tasks:'),
                        TD(quotas.get('ntasks'),
                           klass='integer')))
        table = TABLE(TR(TR(TH('Name'),
                         TD(account['name'])),
                      TR(TH('Email'),
                         TD(account['email'] or '')),
                      TR(TH('Description'),
                         TD(self.to_html(account['description']))),
                      TR(TH('Statistics'),
                         TD(stats))))
        return table


class Account(MethodMixin, GET):
    "Display account information."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                AccountHtmlRepresentation]

    def set_current(self, request):
        self.set_current_account(request)

    def is_accessible(self):
        if self.is_login_admin(): return True
        if self.account['name'] == self.login['name']: return True
        if self.account['name'] == 'anonymous': return True
        return False

    def get_data_resource(self, request):
        account = self.account.copy()
        statistics = self.db.get_statistics(account['name'])
        statistics['href'] = request.application.get_url('tasks',
                                                         account['name'])
        account['statistics'] = statistics
        account['quotas'] = configuration.get_account_quotas(account)
        return dict(title="Account %(name)s" % account,
                    account=account)

    def get_data_operations(self, request):
        name = self.account['name']
        if configuration.ACCOUNT_BASE_URL_TEMPLATE and name != 'anonymous':
            return [dict(title='Edit account',
                         href=configuration.ACCOUNT_BASE_URL_TEMPLATE % name)]
        else:
            return []
