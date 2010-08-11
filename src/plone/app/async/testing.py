import datetime
import time
import transaction
from uuid import uuid1
from zope import component
from zope.app.appsetup.interfaces import DatabaseOpened
from Testing import ZopeTestCase
from Products.Five import zcml
from Products.Five import fiveconfigure
from zc.async import dispatcher
from zc.async.subscribers import queue_installer,\
    threaded_dispatcher_installer, agent_installer
from zc.async.subscribers import ThreadedDispatcherInstaller
from zc.async.interfaces import IDispatcherActivated, COMPLETED
from zc.async.testing import tear_down_dispatcher
from collective.testcaselayer.ptc import BasePTCLayer, ptc_layer
from collective.testcaselayer.sandbox import Sandboxed
from plone.app.async.interfaces import IAsyncDatabase, IQueueReady, IAsyncService
from plone.app.async.subscribers import notifyQueueReady, configureQueue


def cleanUpQuotas():
    """Reset quotas between tests.

    'job never completed' errors may leave uncollectable jobs in quotas.
    """
    transaction.commit()
    service = component.getUtility(IAsyncService)
    queue = service.getQueues()['']
    for quota in queue.quotas.values():
        queue.quotas.create(quota.name, quota.size)


class AsyncLayer(BasePTCLayer):

    def afterSetUp(self):
        fiveconfigure.debug_mode = True
        import plone.app.async
        zcml.load_config('configure.zcml', plone.app.async)
        fiveconfigure.debug_mode = False

        async_db = ZopeTestCase.app()._p_jar.db()
        component.provideUtility(async_db, IAsyncDatabase)
        component.provideHandler(agent_installer, [IDispatcherActivated])
        component.provideHandler(notifyQueueReady, [IDispatcherActivated])
        component.provideHandler(configureQueue, [IQueueReady])
        event = DatabaseOpened(async_db)
        threaded_dispatcher_installer.poll_interval = 0.5
        queue_installer(event)
        threaded_dispatcher_installer(event)

    def beforeTearDown(self):
        gsm = component.getGlobalSiteManager()
        async_db = gsm.getUtility(IAsyncDatabase)
        gsm.unregisterUtility(async_db, IAsyncDatabase)
        gsm.unregisterHandler(agent_installer, [IDispatcherActivated])
        dispatcher_object = dispatcher.get()
        if dispatcher_object is not None:
            tear_down_dispatcher(dispatcher_object)


async_layer = AsyncLayer(bases=[ptc_layer])


class AsyncSandboxed(Sandboxed):
    '''Derive from this class and an xTestCase to make each test
       run in its own ZODB sandbox::

           class MyTest(AsyncSandboxed, ZopeTestCase):
               ...

        This mix-in requires the use of the layer.AsyncLayer layer to be
        installed.
    '''

    def _app(self):
        '''Returns the app object for a test.'''
        # Store an already registered async database (from the testlayer)
        # for later restoration
        self.layer_db = component.getUtility(IAsyncDatabase)

        # DemoStorage connection and friends
        app = super(AsyncSandboxed, self)._app()

        # Register the demostorage as the current async db
        async_db = app._p_jar.db()
        component.provideUtility(async_db, IAsyncDatabase)

        # Create a async dispatcher for this sandbox
        self.dispatcher_uuid = uuid = uuid1()
        event = DatabaseOpened(async_db)
        ThreadedDispatcherInstaller(poll_interval=0.5, uuid=uuid)(event)

        return app

    def _close(self):
        '''Clears the transaction and the AppZapper.'''
        # Clear the dispatcher
        sbdispatcher = dispatcher.get(self.dispatcher_uuid)
        # Transaction manager lost track of the database connection??
        transaction.manager.registerSynch(sbdispatcher.conn)
        tear_down_dispatcher(sbdispatcher)
        dispatcher.pop(self.dispatcher_uuid)

        # Demostorage cleanup (and such)
        super(AsyncSandboxed, self)._close()

        # re-instate the underlying (layer) storage as the async db.
        component.provideUtility(self.layer_db, IAsyncDatabase)

        # Re-activate the layer dispatcher
        dispatcher.get().activated = datetime.datetime.now()


#
# Utility Functions
#

def wait_until_all_jobs_complete(seconds=10):
    """Wait for all jobs in the queue to be complete"""
    queue = component.getUtility(IAsyncService).getQueues()['']
    for i in range(seconds * 10):
        transaction.begin()
        incomplete = [j for j in queue if j.status != COMPLETED]
        if not incomplete:
            break
        time.sleep(0.1)
    else:
        assert False, 'Jobs never completed'
