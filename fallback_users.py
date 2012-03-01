""" Adhoc: Simple web application for task execution.

Fallback interface when there is no WhoYou service.
"""

def get_account(name, password=None):
    """Get the account data dictionary containing items:
    - name: str
    - description: str or None
    - email: str or None
    - teams: list of str
    - properties: dict
    If the password is given, then authenticate.
    Raise KeyError if no such account.
    Raise ValueError if incorrect password.
    """
    return dict(name=name,
                description='Dummy account',
                email=None,
                teams=[],
                properties=dict())

def get_accounts():
    "Return a list of all accounts as dictionaries."
    return [get_account('dummy')]

def get_team(name):
    """Get the team data dictionary containing items:
    - name: str
    - description: str or None
    - members: list of str
    - admins: list of str
    - properties: dict
    Raise KeyError if no such team.
    """
    return dict(name=name,
                description='Dummy team',
                members=[],
                admins=[],
                properties=dict())

def update_account_properties(name, applicationname, properties):
    "Update the properties of the given account for the given application."
    pass
