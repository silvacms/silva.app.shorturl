import unittest

from zope import component
from zope.interface.verify import verifyObject

from silva.core.interfaces import ISiteManager

from ..testing import FunctionalLayer
from ..interfaces import IShortURLService, IShortURLResolverService


class CustomShortURLServiceTestCase(unittest.TestCase):

    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addPublication('pub', 'Publication')
        factory = self.root.pub.manage_addProduct['Silva']
        factory.manage_addMockupVersionedContent('something', 'Some Content')
        factory.manage_addMockupVersionedContent('other', 'Other Content')

        self.content = self.root.pub.something

    def test_verify_service(self):
        short_url = component.queryUtility(IShortURLService)
        self.assertTrue(verifyObject(IShortURLService, short_url))

    def test_verify_local_service(self):
        ISiteManager(self.root.pub).make_site()
        factory = self.root.pub.manage_addProduct['silva.app.shorturl']
        factory.manage_addShortURLService()
        local_service = self.root.pub.service_shorturls
        self.assertTrue(verifyObject(IShortURLService, local_service))

    def test_verify_resolver(self):
        service = component.queryUtility(IShortURLResolverService)
        self.assertTrue(verifyObject(IShortURLResolverService, service))

    def test_name_chooser(self):
        ISiteManager(self.root.pub).make_site()
        factory = self.root.pub.manage_addProduct['silva.app.shorturl']
        factory.manage_addShortURLService()
        local_service = self.root.pub.service_shorturls

        self.assertTrue(self.root.pub.something)
        local_service.register_custom_short_path('ST', self.content.something)
        factory = self.root.pub.manage_addProduct['Silva']

        with self.assertRaises(ValueError):
            factory.manage_addMockupVersionedContent('ST', 'Some Content')



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CustomShortURLServiceTestCase))
    return suite
