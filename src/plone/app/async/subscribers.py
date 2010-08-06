import logging
import transaction
from zope.component import getUtility
from zope.event import notify
from zc.async.interfaces import KEY
from plone.app.async.interfaces import IAsyncDatabase
from plone.app.async.interfaces import QueueReady

logger = logging.getLogger('plone.app.async')


def set_quota(queue, quota_name, size):
    """Create quota or modify existing."""
    if quota_name in queue.quotas:
        queue.quotas[quota_name].size = size
        logger.info("Configured quota %r in queue %r", quota_name, queue.name)
    else:
        queue.quotas.create(quota_name, size=size)
        logger.info("Quota %r added to queue %r", quota_name, queue.name)


def notifyQueueReady(event):
    """Subscriber for IDispatcherActivated."""
    async_db = getUtility(IAsyncDatabase)
    tm = transaction.TransactionManager()
    conn = async_db.open(transaction_manager=tm)
    tm.begin()
    try:
        try:
            queues = conn.root()[KEY]
            for queue in queues.values():
                notify(QueueReady(queue))
            tm.commit()
        except:
            tm.abort()
            raise
    finally:
        conn.close()


def configureQueue(event):
    """Subscriber for IQueueReady."""
    queue = event.object
    if queue.name == '':
        set_quota(queue, 'default', size=1)
