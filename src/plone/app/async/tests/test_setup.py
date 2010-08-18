import transaction
from zope.component import queryUtility
from zc.async import dispatcher
from zc.async.testing import wait_for_result
from plone.app.async.interfaces import IAsyncDatabase
from plone.app.async.tests.base import AsyncTestCase


def dbUsed(context):
    return str(context._p_jar.db())


class TestSetup(AsyncTestCase):
    """
    """

    def test_async_db_present(self):
        self.failUnless(queryUtility(IAsyncDatabase) is not None)

    def test_dispatcher_present(self):
        self.failUnless(dispatcher.get() is not None)

    def test_queues_present(self):
        self.failUnless(self.async.getQueues() is not None)

    def test_quotas_present(self):
        self.failUnless(self.async.getQueues()[''].quotas.get('default') is not None)

    def test_same_db(self):
        """Tests whether the dispatcher sees the same db.
        """
        job = self.async.queueJob(dbUsed, self.folder)
        transaction.commit()
        wait_for_result(job)
        self.assertEqual(job.result, str(self.app._p_jar.db()))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestSetup))
    return suite
