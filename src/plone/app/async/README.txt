User Documentation
------------------

Assuming your setup is done correctly, you can start by obtaining the `AsyncService` utility:

    >>> from zope.component import getUtility
    >>> from plone.app.async.interfaces import IAsyncService
    >>> asyncService = getUtility(IAsyncService)
    >>> asyncService
    <plone.app.async.service.AsyncService object at ...>

You can already get the zc.async queues:

    >>> asyncService.getQueues()
    <zc.async.queue.Queues object at ...>

    >>> import zc.async.dispatcher
    >>> zc.async.dispatcher.get()
    <zc.async.dispatcher.Dispatcher object at ...>
    >>> queue = asyncService.getQueues()['']
    >>> queue
    <zc.async.queue.Queue object at ...>

Make sure that the dispatcher sees the same db:

    >>> import transaction
    >>> from zc.async.testing import wait_for_result
    >>> def dbUsed(context):
    ...     return str(context._p_jar.db())
    >>> job = asyncService.queueJob(dbUsed, self.folder)
    >>> transaction.commit()
    >>> disp_db = wait_for_result(job)
    >>> disp_db == str(self.folder._p_jar.db())
    True


Let's define a simple function to be executed asynchronously:

    >>> def addNumbers(context, x1, x2):
    ...     return x1+x2

and queue it:

    >>> job = asyncService.queueJob(addNumbers, self.folder, 40, 2)
    >>> len(queue)
    1
    >>> transaction.commit()

For the sake of the test we should wait for the job to complete:

    >>> wait_for_result(job)
    42
