from zope.component import getUtility
from Products.PloneTestCase import PloneTestCase
from plone.app.async.testing import AsyncSandboxed, async_layer
from plone.app.async.testing import cleanUpQuotas
from plone.app.async.interfaces import IAsyncService


PloneTestCase.setupPloneSite()


class AsyncTestCase(AsyncSandboxed, PloneTestCase.PloneTestCase):
    """We use this base class for all the tests in this package.
    """
    layer = async_layer

    def afterSetUp(self):
        self.async = getUtility(IAsyncService)

    def beforeTearDown(self):
        # always clean up any existing quotas
        cleanUpQuotas()
