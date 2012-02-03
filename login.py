""" Adhoc: Simple web application for task execution.

Login resource.
"""

from .method_mixin import *


class GET_Login(MethodMixin, GET):
    "Login to an account."

    def handle(self, resource, request, application):
        "If not logged in, then do so. Redirect to account page."
        if self.login.name == 'anonymous':
            raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=application.name)
        self.redirect = "%s/account/%s" % (application.url, self.login.name)
        # The cookie remedies an apparent deficiency of several
        # human browsers: For some pages in the site (notably
        # the application root '/'), the authentication data does not
        # seem to be sent voluntarily by the browser.
        self.cookie = "%s-login=yes; Path=%s" % (application.name,
                                                 application.path)

    def get_response(self, resource, request, application):
        return HTTP_SEE_OTHER(Location=self.redirect, Set_Cookie=self.cookie)
