from zope import interface
from zope.component.interfaces import IObjectEvent


class IInitAsync(interface.Interface):

    def init():
        """ init zc.async """


class IAsyncDatabase(interface.Interface):
    """ zc.async database """


class IAsyncService(interface.Interface):
    """Utility
    """

    def queueJob():
        """Queue a job.
        """

    def queueJobInQueue():
        """Queue a job in a specific queue.
        """


class IQueueReady(IObjectEvent):
    """Queue is ready"""


class QueueReady(object):
    interface.implements(IQueueReady)

    def __init__(self, object):
        self.object = object

class IJobSuccess(IObjectEvent):
    """Job was completed successfully"""


class JobSuccess(object):
    interface.implements(IJobSuccess)

    def __init__(self, object):
        self.object = object


class IJobFailure(IObjectEvent):
    """Job has failed"""


class JobFailure(object):
    interface.implements(IJobFailure)

    def __init__(self, object):
        self.object = object
