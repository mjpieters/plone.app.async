import time
import transaction
import Zope2
import uuid
from zope import component
from zope.app.appsetup.interfaces import DatabaseOpened
from Products.Five import zcml
from Products.Five import fiveconfigure
from zc.async import dispatcher
from zc.async.subscribers import queue_installer, agent_installer
from zc.async.subscribers import ThreadedDispatcherInstaller
from zc.twist import Failure
from zc.async.interfaces import IDispatcherActivated
from zc.async.testing import wait_for_result
from zc.async.testing import tear_down_dispatcher
from Products.PloneTestCase import ptc
from collective.testcaselayer.ptc import BasePTCLayer, ptc_layer
from plone.app.async.interfaces import IAsyncDatabase, IQueueReady, IAsyncService
from plone.app.async.subscribers import notifyQueueReady, configureQueue

_dispatcher_uuid = uuid.uuid1()
_async_layer_db = None


def cleanUpQuotas():
    service = component.queryUtility(IAsyncService)
    if service is not None:
        queue = service.getQueues()['']
        queue.quotas.remove('default')


def cleanUpDispatcher(uuid=None):
    dispatcher_object = dispatcher.get(uuid)
    if dispatcher_object is not None:
        tear_down_dispatcher(dispatcher_object)
        dispatcher.pop(dispatcher_object.UUID)


def setUpDispatcher(db, uuid=None):
    event = DatabaseOpened(db)
    ThreadedDispatcherInstaller(poll_interval=0.1, uuid=uuid)(event)
    time.sleep(0.2)


class AsyncLayer(BasePTCLayer):

    def afterSetUp(self):
        fiveconfigure.debug_mode = True
        import plone.app.async
        zcml.load_config('configure.zcml', plone.app.async)
        fiveconfigure.debug_mode = False
        global _async_layer_db
        async_db = _async_layer_db = self.app._p_jar.db()
        component.provideUtility(async_db, IAsyncDatabase)
        component.provideHandler(agent_installer, [IDispatcherActivated])
        component.provideHandler(notifyQueueReady, [IDispatcherActivated])
        component.provideHandler(configureQueue, [IQueueReady])
        event = DatabaseOpened(async_db)
        queue_installer(event)
        setUpDispatcher(async_db, _dispatcher_uuid)
        transaction.commit()

    def beforeTearDown(self):
        cleanUpDispatcher(_dispatcher_uuid)
        async_db = self.app._p_jar.db()
        gsm = component.getGlobalSiteManager()
        gsm.unregisterUtility(async_db, IAsyncDatabase)
        gsm.unregisterHandler(agent_installer, [IDispatcherActivated])
        gsm.unregisterHandler(notifyQueueReady, [IDispatcherActivated])
        gsm.unregisterHandler(configureQueue, [IQueueReady])

async_layer = AsyncLayer(bases=[ptc_layer])


class AsyncSandbox(ptc.Sandboxed):

    def afterSetUp(self):
        # The commented should work, but it does not. Would remove all the
        # additional threads.
        #dispatcher.get(_dispatcher_uuid).activated = False
        cleanUpDispatcher(_dispatcher_uuid)
        db = async_db = self.app._p_jar.db()
        component.provideUtility(async_db, IAsyncDatabase)
        setUpDispatcher(async_db)
        transaction.commit()
        self._stuff = Zope2.bobo_application._stuff
        Zope2.bobo_application._stuff = (db,) + self._stuff[1:]

    def beforeTearDown(self):
        cleanUpQuotas()
        cleanUpDispatcher()
        component.provideUtility(_async_layer_db, IAsyncDatabase)
        setUpDispatcher(_async_layer_db, _dispatcher_uuid)
        #dispatcher.get(_dispatcher_uuid).activate()
        transaction.commit()
        Zope2.bobo_application._stuff = self._stuff


def wait_for_all_jobs(seconds=6, assert_successful=True):
    """Wait for all jobs in the queue to complete"""
    transaction.begin()
    service = component.getUtility(IAsyncService)
    queue = service.getQueues()['']
    for job in queue:
        wait_for_result(job, seconds)
        if assert_successful:
            assert not isinstance(job.result, Failure), str(job.result)
    # Sync the db
    transaction.commit()
