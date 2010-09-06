import time
import transaction
import Zope2
import uuid
from zope import component
from zope.app.appsetup.interfaces import DatabaseOpened
from ZODB import DB
from ZODB.DemoStorage import DemoStorage
from Products.Five import zcml
from Products.Five import fiveconfigure
from zc.async import dispatcher
from zc.async.subscribers import QueueInstaller
from zc.async.subscribers import ThreadedDispatcherInstaller
from zc.async.subscribers import agent_installer
from zc.async.interfaces import IDispatcherActivated
from zc.async.testing import tear_down_dispatcher
from Products.PloneTestCase import ptc
from collective.testcaselayer.ptc import BasePTCLayer, ptc_layer
from plone.app.async.interfaces import IAsyncDatabase, IQueueReady
from plone.app.async.subscribers import notifyQueueReady, configureQueue


_dispatcher_uuid = uuid.uuid1()
_async_layer_db = None


def createAsyncDB(main_db):
    async_db = DB(DemoStorage(), database_name='async')
    async_db.databases['unnamed'] = main_db # Fake dbtab
    main_db.databases['async'] = async_db   # Fake dbtab
    return async_db


def setUpQueue(db):
    event = DatabaseOpened(db)
    QueueInstaller()(event)


def setUpDispatcher(db, uuid=None):
    event = DatabaseOpened(db)
    ThreadedDispatcherInstaller(poll_interval=0.2, uuid=uuid)(event)
    time.sleep(0.1) # Allow the thread to start up


def cleanUpDispatcher(uuid=None):
    dispatcher_object = dispatcher.get(uuid)
    if dispatcher_object is not None:
        tear_down_dispatcher(dispatcher_object)
        dispatcher.pop(dispatcher_object.UUID)


class AsyncLayer(BasePTCLayer):

    def afterSetUp(self):
        fiveconfigure.debug_mode = True
        import plone.app.async
        zcml.load_config('configure.zcml', plone.app.async)
        fiveconfigure.debug_mode = False
        global _async_layer_db
        main_db = self.app._p_jar.db()
        _async_layer_db = createAsyncDB(main_db)
        component.provideUtility(_async_layer_db, IAsyncDatabase)
        component.provideHandler(agent_installer, [IDispatcherActivated])
        component.provideHandler(notifyQueueReady, [IDispatcherActivated])
        component.provideHandler(configureQueue, [IQueueReady])
        setUpQueue(_async_layer_db)
        setUpDispatcher(_async_layer_db, _dispatcher_uuid)
        transaction.commit()

    def afterClear(self):
        cleanUpDispatcher(_dispatcher_uuid)
        gsm = component.getGlobalSiteManager()
        gsm.unregisterUtility(_async_layer_db, IAsyncDatabase)
        gsm.unregisterHandler(agent_installer, [IDispatcherActivated])
        gsm.unregisterHandler(notifyQueueReady, [IDispatcherActivated])
        gsm.unregisterHandler(configureQueue, [IQueueReady])

async_layer = AsyncLayer(bases=[ptc_layer])


class AsyncSandbox(ptc.Sandboxed):

    def afterSetUp(self):
        main_db = self.app._p_jar.db()
        async_db = createAsyncDB(main_db)
        component.provideUtility(async_db, IAsyncDatabase)
        setUpQueue(async_db)
        setUpDispatcher(async_db)
        transaction.commit()
        self._stuff = Zope2.bobo_application._stuff
        Zope2.bobo_application._stuff = (main_db,) + self._stuff[1:]

    def afterClear(self):
        cleanUpDispatcher()
        component.provideUtility(_async_layer_db, IAsyncDatabase)
        if hasattr(self, '_stuff'):
            Zope2.bobo_application._stuff = self._stuff
