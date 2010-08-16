import doctest
from Testing import ZopeTestCase
from Products.PloneTestCase import ptc
from plone.app.async.tests.base import FunctionalAsyncTestCase
from plone.app.async.testing import async_layer

optionflags = (doctest.REPORT_ONLY_FIRST_FAILURE |
               doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)


def test_suite():
    suite = ZopeTestCase.FunctionalDocFileSuite(
            'README.txt', package='plone.app.async',
            test_class=FunctionalAsyncTestCase,
            optionflags=optionflags)
    return suite
