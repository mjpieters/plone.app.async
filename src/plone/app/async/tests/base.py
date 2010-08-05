from Products.PloneTestCase import PloneTestCase
from Products.Five.testbrowser import Browser
from plone.app.async.tests.layer import AsyncLayer
PloneTestCase.setupPloneSite()

def setDatabase(db=None):
    """Set the database for the dispatcher thread."""
    import Zope2

    if db is None:
        Zope2.bobo_application._stuff = (Zope2.DB,) + Zope2.bobo_application._stuff[1:]
    else:
        Zope2.bobo_application._stuff = (db,) + Zope2.bobo_application._stuff[1:]

class AsyncTestCase(PloneTestCase.PloneTestCase):
    """We use this base class for all the tests in this package.
    """
    layer = AsyncLayer


class FunctionalAsyncTestCase(PloneTestCase.Functional, AsyncTestCase):
    """For functional tests.
    """
    layer = AsyncLayer

    def getCredentials(self):
        return '%s:%s' % (PloneTestCase.default_user,
            PloneTestCase.default_password)

    def getBrowser(self, loggedIn=True):
        """ instantiate and return a testbrowser for convenience """
        browser = Browser()
        if loggedIn:
            auth = 'Basic %s' % self.getCredentials()
            browser.addHeader('Authorization', auth)
        return browser
