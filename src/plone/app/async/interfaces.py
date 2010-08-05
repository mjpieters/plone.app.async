from zope import interface
from zope.component.interfaces import IObjectEvent


class IInitAsync(interface.Interface):

    def init():
        """ init zc.async """


class IAsyncDatabase(interface.Interface):
    """ zc.async database """


class IQueueReady(IObjectEvent):
    """Queue is ready"""


class IAsyncService(interface.Interface):
    """Utility
    """

    def queueJob():
        """Queue a job.
        """

    def queueJobInQueue():
        """Queue a job in a specific queue.
        """


class QueueReady(object):
    interface.implements(IQueueReady)

    def __init__(self, object):
        self.object = object
