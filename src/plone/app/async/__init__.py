import logging
from Products.CMFCore.interfaces import ISiteRoot
from zc.async.interfaces import KEY
from zope.component import getUtility

logger = logging.getLogger('plone.app.async')
    
def initialize(context):
    """Initializer called when used as a Zope 2 product."""
