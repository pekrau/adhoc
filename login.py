""" Adhoc web resource: simple bioinformatics tasks.

Login resource.
"""

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
            raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=configuration.NAME)
        else:
            # The cookie remedies an apparent deficiency of several
            # human browsers: For some pages in the site (notably
            # the application root '/'), the authentication data does not
            # seem to be sent voluntarily by the browser.
            cookie = "%s-login=yes; Path=%s" % (configuration.NAME,
                                                application.path)
            url = "%s/account/%s" % (application.url, self.login.name)
            raise HTTP_SEE_OTHER(Location=url, Set_Cookie=cookie)
