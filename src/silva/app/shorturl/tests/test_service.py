import unittest

from zope.interface import alsoProvides
from zope import component

from ..testing import FunctionalLayer
from ..interfaces import IShortURLMarker, IShortURLService


class ShortURLServiceTestCase(unittest.TestCase):

    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('folder', 'Folder')
        self.folder = self.root.folder
        factory = self.folder.manage_addProduct['Silva']
        factory.manage_addMockupVersionedContent('something', 'Some Content')
        self.content = self.folder.something
        self.service = component.getUtility(IShortURLService)
        alsoProvides(self.root, IShortURLMarker)

    def test_content_short_path(self):
        short_path = self.service.get_short_path(self.content)
        self.assertIsInstance(short_path, str)
        self.assertEqual(self.service.get_content(short_path), self.content)

    def test_custom_path(self):
        self.service.register_custom_short_path('short', self.content)
        self.assertEqual('short',
            self.service.get_registered_short_path(self.content))
        self.assertEqual(self.content,
            self.service.get_content_from_custom_short_path('short'))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ShortURLServiceTestCase))
    return suite
