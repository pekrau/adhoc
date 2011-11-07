""" Adhoc web resource: simple bioinformatics tasks.

Login resource.
"""

from Cookie import SimpleCookie

from wrapid.response import HTTP_UNAUTHORIZED_BASIC_CHALLENGE, HTTP_SEE_OTHER

from . import configuration
from .method_mixin import BaseMixin


class GET_Login(BaseMixin):
    "Login to an account."

    def __call__(self, resource, request, application):
        """Handle the request and return a response instance.
        If not logged in, then do so. Redirect to account page.
        """
        self.connect(resource, request, application)
        if self.login.name == 'anonymous':
            raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=configuration.REALM)
        else:
            url = "%s/account/%s" % (application.url, self.login.name)
            # The following remedies an apparent deficiency of several
            # human browsers: For some pages in the site (notably
            # the root '/'), the authentication data does not seem to be
            # sent voluntarily by the browser.
            cookie = SimpleCookie()
            key = "%s-login" % configuration.NAME
            cookie[key] = 'yes'
            cookie[key]['path'] = application.path
            raise HTTP_SEE_OTHER(Location=url, Set_Cookie=str(cookie))
