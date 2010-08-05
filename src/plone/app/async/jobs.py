from zope.component import getUtility
from zope.app.component.hooks import setSite
from AccessControl.SecurityManagement import noSecurityManager,\
    newSecurityManager
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from zc.async.job import serial, parallel, Job
from plone.app.async import getQueues


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


def queueJobInQueue(queue, quota, func, context, *args, **kwargs):
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


def queueJob(func, context, *args, **kwargs):
    queue = getQueues()['']
    return queueJobInQueue(queue, ('default',), func, context, *args, **kwargs)


def _queueParallelSerialJobs(jobs, serialize=True):
    portal= getUtility(ISiteRoot)
    portal_path = portal.getPhysicalPath()
    pm = getToolByName(portal, 'portal_membership')
    user_id = pm.getAuthenticatedMember().getId()
    scheduled = []
    for func, context, args, kwargs in jobs:
        context_path = context.getPhysicalPath()
        job = Job(_executeAsUser, portal_path, context_path, user_id,
                  func, *args, **kwargs)
        scheduled.append(job)
    queue = getQueues()['']
    if serialize:
        job = queue.put(serial(*scheduled))
    else:
        job = queue.put(parallel(*scheduled))
    return job


def queueSerialJobs(*jobs):
    return _queueParallelSerialJobs(jobs, serialize=True)


def queueParallelJobs(*jobs):
    return _queueParallelSerialJobs(jobs, serialize=False)
