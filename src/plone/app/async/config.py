import os
import Zope2
from ZODB.interfaces import IDatabase
from Zope2.App import startup
from App.config import getConfiguration
from AccessControl.SecurityManagement import noSecurityManager

from zope import interface, component
from zope.app.appsetup.interfaces import DatabaseOpened

import zc.monitor
import zc.async.dispatcher
from zc.async import subscribers
from plone.app.async.interfaces import IInitAsync, IAsyncDatabase
from plone.app.async import logger


class InitBase(object):
    interface.implements(IInitAsync)

    dbEvents = ()

    def init(self):
        component.provideUtility(Zope2.DB, IDatabase)

        configuration = getConfiguration()
        for name in configuration.dbtab.listDatabaseNames():
            db = configuration.dbtab.getDatabase(name=name)
            component.provideUtility(db, IDatabase, name=name)

        db = configuration.dbtab.getDatabase(name='main')
        component.provideUtility(db, IAsyncDatabase)

        ev = DatabaseOpened(db)
        subscribers.queue_installer(ev)

        for handler in self.dbEvents:
            handler(ev)

        config = configuration.product_config.get('zc.z3monitor')
        if config and 'port' in config:
            logger.info('Starting zc.monitor service on %s port',
                        config['port'])
            zc.monitor.start(int(config['port']))


subscribers.threaded_dispatcher_installer.poll_interval = 2


class InitSingleDBAsync(InitBase):
    dbEvents = (subscribers.threaded_dispatcher_installer,)


def init_zasync():
    noSecurityManager()

    component.getUtility(IInitAsync).init()
    startup.noSecurityManager = noSecurityManager

startup.noSecurityManager = init_zasync


def shutdownDispatcher():
    dispatcher = zc.async.dispatcher.get()
    if dispatcher is not None:
        dispatcher.reactor.callFromThread(dispatcher.reactor.stop)
        dispatcher.thread.join(3)


if os.name == 'nt':
    try:
        from Signals.WinSignalHandler import SignalHandler
    except ImportError:
        pass
        SignalHandler = None
else:
    from Signals.SignalHandler import SignalHandler


if SignalHandler is not None:
    from signal import SIGTERM, SIGINT

    SignalHandler.registerHandler(SIGINT, shutdownDispatcher)
    SignalHandler.registerHandler(SIGTERM, shutdownDispatcher)
