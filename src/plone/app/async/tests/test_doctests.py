import doctest
from zope.testing import module
from Testing import ZopeTestCase
from plone.app.async.tests.base import FunctionalAsyncTestCase

optionflags = (doctest.REPORT_ONLY_FIRST_FAILURE |
               doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)


def modSetUp(test):
   module.setUp(test, 'plone.app.async.tests.doctest_test')


def modTearDown(test):
   import transaction
   transaction.abort()
   module.tearDown(test)


def test_suite():
    suite = ZopeTestCase.FunctionalDocFileSuite(
            'README.txt', package='plone.app.async',
            test_class=FunctionalAsyncTestCase,
            optionflags=optionflags,
            setUp=modSetUp, tearDown=modTearDown)
    return suite
