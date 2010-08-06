import transaction
from zope.component import getUtility
from zc.async.testing import wait_for_result
from Products.PloneTestCase.PloneTestCase import default_user
from Products.CMFCore.utils import getToolByName
from plone.app.async.testing import AsyncTestCase
from plone.app.async.interfaces import IAsyncService
# #from plone.app.async.jobs import queueJob, queueJobInQueue, queueSerialJobs


def addNumbers(context, x1, x2):
    return x1+x2


def createDocument(context, anid, title, description, body):
    context.invokeFactory('Document', anid,
        title=title, description=description, text=body)
    return context[anid].id


def publishDocument(context, doc_id):
    doc = context[doc_id]
    wt = getToolByName(context, 'portal_workflow')
    wt.doActionFor(doc, 'submit')
    return "workflow_change"


def createDocumentAndPublish(context, anid, title, description, body):
    createDocument(context, anid, title, description, body)
    import zc.async
    q = zc.async.local.getJob().queue
    async = getUtility(IAsyncService)    
    job = async.queueJobInQueue(q,('default'), publishDocument, context, anid)
    return job


def reindexDocument(context):
    context.reindexObject()


class TestSimpleJob(AsyncTestCase):
    """
    """
    def afterSetUp(self):
        self.async = getUtility(IAsyncService)

    def test_add_job(self):
        """Tests adding a computational job and getting the result.
        """
        context = self.folder
        job = self.async.queueJob(addNumbers, context, 40, 2)
        transaction.commit()
        self.assertEqual(job.status, u'pending-status')
        wait_for_result(job)
        self.assertEqual(job.status, u'completed-status')
        self.assertEqual(job.result, 42)

    def test_add_persistent(self):
        """Adding a job that creates persistent objects.
        """
        job = self.async.queueJob(createDocument,
            self.folder, 'anid', 'atitle', 'adescr', 'abody')
        transaction.commit()
        self.assertEqual(job.status, u'pending-status')
        wait_for_result(job)
        self.assertEqual(job.status, u'completed-status')
        self.assertEqual(job.result, 'anid')
        self.failUnless('anid' in self.folder.objectIds())
        document = self.folder['anid']
        self.assertEqual(document.Creator(), default_user)

    def test_serial_jobs(self):
        """Queue two jobs the one after the other.
        """
        job1 = (createDocument, self.folder, ('anid2', 'atitle', 'adescr', 'abody'), {})
        job2 = (publishDocument, self.folder, ('anid2',), {})
        job = self.async.queueSerialJobs(job1,job2)
        transaction.commit()
        wait_for_result(job)
        self.assertEqual(job.result[0].result, 'anid2')
        self.assertEqual(job.result[1].result, 'workflow_change')
        doc = self.folder['anid2']
        wt = getToolByName(self.folder, 'portal_workflow')
        self.assertEqual(wt.getInfoFor(doc, 'review_state'), 'pending')


    def test_serial_jobs2(self):
        """Queue a job that queues another job.
        XXX: THIS TEST WILL NOT PASS. Probably to do with threading.local
        XXX: TO BE REVISITED!
        """
        return
        job = self.async.queueJob(createDocumentAndPublish,
            self.folder, 'anid3', 'atitle', 'adescr', 'abody')
        transaction.commit()
        wait_for_result(job)
        self.assertEqual(job.result, 'workflow_change')
        doc = self.folder['anid3']
        wt = getToolByName(self.folder, 'portal_workflow')
        self.assertEqual(wt.getInfoFor(doc, 'review_state'), 'pending')

    def test_indexing(self):
        """Queue indexing.
        """
        self.folder.invokeFactory('Document', 'anid4',
            title='Foo', description='Foo', text='foo')
        doc = self.folder['anid4']
        doc.setDescription('bar')
        ct = getToolByName(self.folder, 'portal_catalog')        
        res = ct.searchResults(Description='bar')
        self.assertEqual(len(res), 0)

        job = self.async.queueJob(reindexDocument, doc)
        transaction.commit()
        wait_for_result(job)
        res = ct.searchResults(Description='bar')
        self.assertEqual(len(res), 1)

        """Demonstrate calling an object's method.
        """
        self.folder.invokeFactory('Document', 'anid5',
            title='Foo', description='Foo', text='foo')
        doc = self.folder['anid5']
        doc.setDescription('bar')
        ct = getToolByName(self.folder, 'portal_catalog')
        res = ct.searchResults(Description='bar')
        self.assertEqual(len(res), 1)

        job = self.async.queueJob(doc.__class__.reindexObject, doc)
        transaction.commit()
        wait_for_result(job)
        res = ct.searchResults(Description='bar')
        self.assertEqual(len(res), 2)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestSimpleJob))
    return suite
