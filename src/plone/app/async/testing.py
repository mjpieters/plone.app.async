import time
from zope import component
from zope.app.appsetup.interfaces import DatabaseOpened
from Products.Five import zcml
from Products.Five import fiveconfigure
from zc.async import dispatcher
from zc.async.subscribers import queue_installer,\
    threaded_dispatcher_installer, agent_installer
from zc.twist import Failure
from zc.async.interfaces import IDispatcherActivated
from zc.async.testing import tear_down_dispatcher
from collective.testcaselayer.ptc import BasePTCLayer, ptc_layer
from collective.testcaselayer.sandbox import Sandboxed
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


class AsyncSandbox(Sandboxed):

    def afterSetUp(self):
        async_db = self.app._p_jar.db()
        component.provideUtility(async_db, IAsyncDatabase)
        event = DatabaseOpened(async_db)
        threaded_dispatcher_installer.poll_interval = 0.2
        threaded_dispatcher_installer(event)
        # XXX The dispatcher will need to setup the queue and quotas.
        # so let's give him some time...
        time.sleep(0.1)

    def beforeTearDown(self):
        dispatcher_object = dispatcher.get()
        tear_down_dispatcher(dispatcher_object)
        dispatcher.pop(dispatcher_object.UUID)

    def wait_for_all_jobs(self, assert_successfull=True, seconds=6):
        """Wait for all jobs in the queue to complete"""
        queue = component.getUtility(IAsyncService).getQueues()['']
        for job in queue:
            from zc.async.testing import wait_for_result
            wait_for_result(job, seconds)
            if assert_successfull:
                assert not isinstance(job.result, Failure), str(job.result)
