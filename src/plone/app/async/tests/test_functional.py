from zope.interface import Interface, implements
from zope.component import getUtility
from zope.formlib import form
from plone.app.async.utils import wait_for_all_jobs
from plone.app.form.interfaces import IPlonePageForm
from Products.Five import zcml
from Products.Five.formlib import formbase
from plone.app.async.interfaces import IAsyncService
from plone.app.async.tests.base import FunctionalAsyncTestCase


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
        async = getUtility(IAsyncService)
        async.queueJob(createDocument, self.context,
            'anid', 'atitle', 'adescr', 'abody')

    @form.action(u"Apply")
    def action_submit(self, action, data):
        """
        """
        self.testing()
        return ''

register_view_zcml = """
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:browser="http://namespaces.zope.org/browser">
    <browser:page
      for="*"
      name="testview"
      class="plone.app.async.tests.test_functional.TestView"
      permission="zope2.View"
    />
</configure>
"""


class TestFunctional(FunctionalAsyncTestCase):
    """This test is here to make sure that the FunctionalAsyncTestCase is
    working properly. In order to do we register and load a browser view that
    adds a job.
    """

    def test_view(self):
        zcml.load_string(register_view_zcml)
        browser = self.getBrowser()
        browser.open(self.folder.absolute_url() + "/@@testview")
        browser.getControl("Apply").click()
        wait_for_all_jobs()
        self.failUnless('anid' in self.folder)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestFunctional))
    return suite
