import transaction
from zope.component import provideHandler, getGlobalSiteManager
from zc.async.testing import wait_for_result
from plone.app.async.tests.base import AsyncTestCase
from plone.app.async.interfaces import IJobSuccess, IJobFailure


events = []


def successJob(context):
    return "Success"


def failingJob(context):
    raise RuntimeError("FooBar")


def successHandler(event):
    events.append(event)


def failureHandler(event):
    events.append(event)


class TestResultHandler(AsyncTestCase):

    def afterSetUp(self):
        super(TestResultHandler, self).afterSetUp()
        provideHandler(failureHandler, [IJobFailure])
        provideHandler(successHandler, [IJobSuccess])

    def beforeTearDown(self):
        gsm = getGlobalSiteManager()
        gsm.unregisterHandler(failureHandler, [IJobFailure])
        gsm.unregisterHandler(successHandler, [IJobSuccess])
        super(TestResultHandler, self).beforeTearDown()

    def test_success(self):
        events[:] = []
        job = self.async.queueJob(successJob, self.folder)
        transaction.commit()
        wait_for_result(job)
        self.assertEquals(events[0].object, 'Success')

    def test_failure(self):
        events[:] = []
        job = self.async.queueJob(failingJob, self.folder)
        transaction.commit()
        wait_for_result(job)
        result = events[0].object
        self.assertEquals(str(result.type), 'exceptions.RuntimeError')
        self.assertEquals(str(result.value), 'FooBar')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestResultHandler))
    return suite
