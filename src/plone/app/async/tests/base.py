import datetime
import transaction
import uuid
from zope import component
from Products.PloneTestCase import PloneTestCase
from Products.Five.testbrowser import Browser
from plone.app.async.tests.layer import AsyncLayer
from plone.app.async.interfaces import IAsyncDatabase
from zc.async.subscribers import ThreadedDispatcherInstaller
from zc.async import dispatcher
from zope.app.appsetup.interfaces import DatabaseOpened

PloneTestCase.setupPloneSite()


def setDatabase(db=None):
    """Set the database for the dispatcher thread."""
    import Zope2

    if db is None:
        Zope2.bobo_application._stuff = (Zope2.DB,) + Zope2.bobo_application._stuff[1:]
    else:
        Zope2.bobo_application._stuff = (db,) + Zope2.bobo_application._stuff[1:]


class AsyncSandboxed(PloneTestCase.Sandboxed):
    '''Derive from this class and an xTestCase to make each test
       run in its own ZODB sandbox::

           class MyTest(AsyncSandboxed, ZopeTestCase):
               ...

        This mix-in requires the use of the layer.AsyncLayer layer to be
        installed.
    '''

    _layer_db = None
    _dispatch_uuid = None

    def _app(self):
        '''Returns the app object for a test.'''
        # Store an already registered async database (from the testlayer)
        # for later restoration
        self._layer_db = component.getUtility(IAsyncDatabase)
        gsm = component.getGlobalSiteManager()
        gsm.unregisterUtility(self._layer_db, IAsyncDatabase)

        # Deactivate the layer dispatcher
        dispatcher.get().activated = False

        # DemoStorage connection and friends
        app = PloneTestCase.Sandboxed._app(self)

        # Register the demostorage as the current async db
        async_db = app._p_jar._db
        component.provideUtility(async_db, IAsyncDatabase)
        setDatabase(async_db)

        # Create a async dispatcher for this sandbox
        self._dispatch_uuid = sb_uuid = uuid.uuid1()
        event = DatabaseOpened(async_db)
        ThreadedDispatcherInstaller(poll_interval=0.5, uuid=sb_uuid)(event)

        return app

    def _close(self):
        '''Clears the transaction and the AppZapper.'''
        # Clear the dispatcher
        sbdispatcher = dispatcher.get(self._dispatch_uuid)
        # Transaction manager lost track of the database connection??
        transaction.manager.registerSynch(sbdispatcher.conn)
        sbdispatcher.deactivate()
        dispatcher.pop(self._dispatch_uuid)
        sbdispatcher.thread.join(0.5)

        # Un-register the demo storage
        gsm = component.getGlobalSiteManager()
        async_db = gsm.getUtility(IAsyncDatabase)
        gsm.unregisterUtility(async_db, IAsyncDatabase)

        # Demostorage cleanup (and such)
        PloneTestCase.Sandboxed._close(self)

        # re-instate the underlying (layer) storage as the async db.
        component.provideUtility(self._layer_db, IAsyncDatabase)
        setDatabase(self._layer_db)

        # Re-activate the layer dispatcher
        dispatcher.get().activated = datetime.datetime.now()


class AsyncTestCase(AsyncSandboxed, PloneTestCase.PloneTestCase):
    """We use this base class for all the tests in this package.
    """
    layer = AsyncLayer


class FunctionalAsyncTestCase(PloneTestCase.Functional, AsyncTestCase):
    """For functional tests.
    """
    layer = AsyncLayer

    def getCredentials(self):
        return '%s:%s' % (PloneTestCase.default_user,
            PloneTestCase.default_password)

    def getBrowser(self, loggedIn=True):
        """ instantiate and return a testbrowser for convenience """
        browser = Browser()
        if loggedIn:
            auth = 'Basic %s' % self.getCredentials()
            browser.addHeader('Authorization', auth)
        return browser
