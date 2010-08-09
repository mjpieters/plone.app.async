from zope.component import queryUtility, getUtility
from zc.async import dispatcher
from plone.app.async.interfaces import IAsyncDatabase, IAsyncService
from plone.app.async.tests.base import AsyncTestCase


class TestSetup(AsyncTestCase):
    """
    """

    def test_setup(self):
        """
        """
        self.failUnless(queryUtility(IAsyncDatabase) is not None)
        self.failUnless(dispatcher.get() is not None)
        async = getUtility(IAsyncService)
        self.failUnless(async.getQueues() is not None)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestSetup))
    return suite
