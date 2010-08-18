import transaction
import Zope2
from zope import component
from zope.app.appsetup.interfaces import DatabaseOpened
from Products.Five import zcml
from Products.Five import fiveconfigure
from zc.async import dispatcher
from zc.async.subscribers import queue_installer,\
    threaded_dispatcher_installer, agent_installer
from zc.twist import Failure
from zc.async.interfaces import IDispatcherActivated
from zc.async.testing import wait_for_result
from zc.async.testing import tear_down_dispatcher
from Products.PloneTestCase import ptc
from collective.testcaselayer.ptc import BasePTCLayer, ptc_layer
from plone.app.async.interfaces import IAsyncDatabase, IQueueReady, IAsyncService
from plone.app.async.subscribers import notifyQueueReady, configureQueue


class AsyncLayer(BasePTCLayer):

    def afterSetUp(self):
        fiveconfigure.debug_mode = True
        import plone.app.async
        zcml.load_config('configure.zcml', plone.app.async)
        fiveconfigure.debug_mode = False

        async_db = self.app._p_jar.db()
        component.provideUtility(async_db, IAsyncDatabase)
        component.provideHandler(agent_installer, [IDispatcherActivated])
        component.provideHandler(notifyQueueReady, [IDispatcherActivated])
        component.provideHandler(configureQueue, [IQueueReady])
        event = DatabaseOpened(async_db)
        queue_installer(event)

    def beforeTearDown(self):
        async_db = self.app._p_jar.db()
        gsm = component.getGlobalSiteManager()
        gsm.unregisterUtility(async_db, IAsyncDatabase)
        gsm.unregisterHandler(agent_installer, [IDispatcherActivated])
        gsm.unregisterHandler(notifyQueueReady, [IDispatcherActivated])
        gsm.unregisterHandler(configureQueue, [IQueueReady])

async_layer = AsyncLayer(bases=[ptc_layer])


def cleanUpQuotas():
    service = component.queryUtility(IAsyncService)
    if service is not None:
        queue = service.getQueues()['']
        for quota in queue.quotas.values():
            queue.quotas.create(quota.name, quota.size)


def cleanUpDispatcher():
    dispatcher_object = dispatcher.get()
    if dispatcher_object is not None:
        tear_down_dispatcher(dispatcher_object)
        dispatcher.pop(dispatcher_object.UUID)


class AsyncSandbox(ptc.Sandboxed):

    def afterSetUp(self):
        db = async_db = self.app._p_jar.db()
        component.provideUtility(async_db, IAsyncDatabase)
        cleanUpDispatcher()
        event = DatabaseOpened(async_db)
        threaded_dispatcher_installer.poll_interval = 0.2
        threaded_dispatcher_installer(event)
        transaction.commit()
        self._stuff = Zope2.bobo_application._stuff
        Zope2.bobo_application._stuff = (db,) + self._stuff[1:]

    def beforeTearDown(self):
        cleanUpQuotas()
        cleanUpDispatcher()
        transaction.commit()
        async_db = self.app._p_jar.db()
        gsm = component.getGlobalSiteManager()
        gsm.unregisterUtility(async_db, IAsyncDatabase)
        Zope2.bobo_application._stuff = self._stuff


def wait_for_all_jobs(seconds=6, assert_successful=True):
    """Wait for all jobs in the queue to complete"""
    service = component.getUtility(IAsyncService)
    queue = service.getQueues()['']
    for job in queue:
        wait_for_result(job, seconds)
        if assert_successful:
            assert not isinstance(job.result, Failure), str(job.result)
