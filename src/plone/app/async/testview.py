from zope.interface import Interface, implements
from zope.component import getUtility, getMultiAdapter
from zope import schema
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.formlib import form
from plone.app.form.interfaces import IPlonePageForm
from Products.Five.formlib import formbase
from Products.statusmessages.interfaces import IStatusMessage
from zc.async.job import Job
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces import ISiteRoot
from ZPublisher.Publish import get_module_info
from zope.app.component.hooks import setSite

from AccessControl.SecurityManagement import noSecurityManager, newSecurityManager
import transaction
from plone.app.async.jobs import queueJob
from plone.app.async import getQueues

def createDocument(context, anid, title, description, body):
    context.invokeFactory('Document', anid,
        title=title, description=description, text=body)
    return context[anid].id
    
class IFFields(Interface):
    pass


class TestView(formbase.PageForm):
    """
    """

    implements(IPlonePageForm)
    label = u"Test"
    form_fields = form.Fields(IFFields)

    def testing(self):
        job = queueJob(createDocument, self.context, 'anid2','atitle','adescr','abody')
        return

    @form.action(u"Apply")
    def action_submit(self, action, data):
        """
        """
        self.testing()
        return ''