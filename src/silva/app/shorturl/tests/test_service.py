import unittest

from zope.interface import alsoProvides
from zope import component


from silva.app.forest.interfaces import IForestService

from ..testing import FunctionalLayer
from ..interfaces import IShortURLMarker, IShortURLService


class ServiceActivationTestCase(unittest.TestCase):

    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('manager')
        self.service = component.getUtility(IShortURLService)
        self.forest_service = component.getUtility(IForestService)

    def test_activation_requires_forest(self):
        self.assertFalse(self.forest_service.is_active())
        self.assertFalse(self.service.is_active())

        with self.assertRaises(ValueError):
            self.service.activate()

        self.forest_service.activate()
        self.service.activate()

        self.assertTrue(self.forest_service.is_active())
        self.assertTrue(self.service.is_active())

        self.service.deactivate()
        self.assertFalse(self.service.is_active())

    def test_deactivation_of_forest_deactivate_shorturl(self):
        self.forest_service.activate()
        self.service.activate()
        self.assertTrue(self.service.is_active())

        self.forest_service.deactivate()
        self.assertFalse(self.service.is_active())


class ShortURLServiceTestCase(unittest.TestCase):

    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('folder', 'Folder')
        self.folder = self.root.folder
        factory = self.folder.manage_addProduct['Silva']
        factory.manage_addMockupVersionedContent('something', 'Some Content')
        factory.manage_addMockupVersionedContent('other', 'Other Content')

        self.content = self.folder.something
        self.service = component.getUtility(IShortURLService)
        alsoProvides(self.root, IShortURLMarker)

    def test_content_short_path(self):
        short_path = self.service.get_short_path(self.content)
        self.assertIsInstance(short_path, str)
        self.assertEqual(
            self.service.get_content_from_short_path(short_path),
            self.content)

    def test_custom_path(self):
        self.service.register_custom_short_path('short', self.content)
        self.assertEqual('short',
            self.service.get_custom_short_path(self.content))
        self.assertEqual(self.content,
            self.service.get_content_from_custom_short_path('short'))

    def test_get_content(self):
        short_path = self.service.get_short_path(self.content)
        self.service.register_custom_short_path(short_path, self.folder.other)
        self.assertEqual(self.folder.other,
            self.service.get_content(short_path))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ServiceActivationTestCase))    
    suite.addTest(unittest.makeSuite(ShortURLServiceTestCase))
    return suite
