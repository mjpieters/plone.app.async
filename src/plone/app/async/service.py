from zope.component import getUtility
from zope.interface import implements
from zope.app.component.hooks import setSite
from AccessControl.SecurityManagement import noSecurityManager,\
    newSecurityManager
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from zc.async.interfaces import KEY
from zc.async.job import serial, parallel, Job
from plone.app.async.interfaces import IAsyncService


def makeJob(func, context, *args, **kwargs):
    """Return a job info tuple."""
    return (func, context, args, kwargs)

def _executeAsUser(portal_path, context_path, user_id, func, *args, **kwargs):
    import Zope2
    transaction = Zope2.zpublisher_transactions_manager # Supports isDoomed
    transaction.begin()
    app = Zope2.app()
    success = False
    result = None
    try:
        portal = app.unrestrictedTraverse(portal_path, None)
        if portal is None:
            return
        setSite(portal)

        acl_users = getToolByName(portal, 'acl_users')
        user = acl_users.getUserById(user_id)
        if user is None:
            return
        if not hasattr(user, 'aq_base'):
            user = user.__of__(acl_users)
        newSecurityManager(None, user)

        context = portal.unrestrictedTraverse(context_path, None)
        if context is None:
            return
        result = func(context, *args, **kwargs)
        transaction.commit()
        success = True

    finally:
        if not success:
            transaction.abort()
        noSecurityManager()
        setSite(None)
        app._p_jar.close()
    return result


class AsyncService(object):
    implements(IAsyncService)

    def getQueues(self):
        portal = getUtility(ISiteRoot)
        return portal._p_jar.root()[KEY]

    def queueJob(self, func, context, *args, **kwargs):
        queue = self.getQueues()['']
        return self.queueJobInQueue(queue, ('default',), func, context, *args, **kwargs)

    def queueJobInQueue(self, queue, quota, func, context, *args, **kwargs):
        pm = getToolByName(context, 'portal_membership')
        user_id = pm.getAuthenticatedMember().getId()
        portal_path = getUtility(ISiteRoot).getPhysicalPath()
        context_path = context.getPhysicalPath()
        job = Job(_executeAsUser, portal_path, context_path, user_id,
                  func, *args, **kwargs)
        if quota:
            job.quota_names = quota
        job = queue.put(job)
        return job

    def _queueJobsInQueue(self, queue, quota_names, job_infos, serialize=True):
        portal = getUtility(ISiteRoot)
        portal_path = portal.getPhysicalPath()
        pm = getToolByName(portal, 'portal_membership')
        user_id = pm.getAuthenticatedMember().getId()
        scheduled = []
        for (func, context, args, kwargs) in job_infos:
            context_path = context.getPhysicalPath()
            job = Job(_executeAsUser, portal_path, context_path, user_id,
                      func, *args, **kwargs)
            scheduled.append(job)
        if serialize:
            job = serial(*scheduled)
        else:
            job = parallel(*scheduled)
        if quota_names:
            job.quota_names = quota_names
        job = queue.put(job)
        return job

    def queueSerialJobsInQueue(self, queue, quota_names, *job_infos):
        return self._queueJobsInQueue(queue, quota_names, job_infos, serialize=True)

    def queueParallelJobsInQueue(self, queue, quota_names, *job_infos):
        return self._queueJobsInQueue(queue, quota_names, job_infos, serialize=False)

    def queueSerialJobs(self, *job_infos):
        queue = self.getQueues()['']
        return self.queueSerialJobsInQueue(queue, ('default',), *job_infos)

    def queueParallelJobs(self, *job_infos):
        queue = self.getQueues()['']
        return self.queueParallelJobsInQueue(queue, ('default',), *job_infos)
