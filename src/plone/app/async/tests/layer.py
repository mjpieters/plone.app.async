from zope.component import provideUtility, getGlobalSiteManager, provideHandler
from zope.app.appsetup.interfaces import DatabaseOpened
from Testing import ZopeTestCase
from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase.layer import PloneSite
from zc.async.subscribers import queue_installer,\
    threaded_dispatcher_installer, agent_installer
from zc.async import dispatcher
from zc.async.interfaces import IDispatcherActivated
from plone.app.async.interfaces import IAsyncDatabase, IQueueReady
from plone.app.async.subscribers import notifyQueueReady, configureQueue
class AsyncLayer(PloneSite):

    @classmethod
    def setUp(cls):
        fiveconfigure.debug_mode = True
        import plone.app.async
        zcml.load_config('configure.zcml', plone.app.async)
        fiveconfigure.debug_mode = False
        
        async_db = ZopeTestCase.app()._p_jar._db
        provideUtility(async_db, IAsyncDatabase)
        provideHandler(agent_installer, [IDispatcherActivated])
        provideHandler(notifyQueueReady, [IDispatcherActivated])
        provideHandler(configureQueue, [IQueueReady])
        event = DatabaseOpened(async_db)
        threaded_dispatcher_installer.poll_interval = 0.5
        queue_installer(event)
        threaded_dispatcher_installer(event)

    @classmethod
    def tearDown(cls):
        async_db = getGlobalSiteManager().getUtility(IAsyncDatabase)
        gsm = getGlobalSiteManager()
        gsm.unregisterUtility(async_db, IAsyncDatabase)
        gsm.unregisterHandler(agent_installer, [IDispatcherActivated])
        dispatcher_object = dispatcher.get()
        if dispatcher_object is not None:
            dispatcher_object.reactor.callFromThread(
                dispatcher_object.reactor.stop)
            dispatcher_object.thread.join(3)
