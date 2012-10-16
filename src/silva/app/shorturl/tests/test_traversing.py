import unittest

from zope.interface import alsoProvides
from zope import component

from silva.core.layout.interfaces import IMarkManager
from silva.core.interfaces import IPublicationWorkflow

from ..testing import FunctionalLayer
from ..interfaces import IShortURLMarker, IShortURLService


class TraversingTestCase(unittest.TestCase):

    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('folder', 'Folder')
        self.folder = self.root.folder
        factory = self.folder.manage_addProduct['Silva']
        factory.manage_addMockupVersionedContent('something', 'Some Content')
        self.content = self.folder.something
        self.layer.login('manager')
        IPublicationWorkflow(self.content).publish()
        self.layer.logout()
        self.service = component.getUtility(IShortURLService)

    def test_traverse_without_marker(self):
        short_path = self.service.get_short_path(self.content)
        with self.layer.get_browser() as browser:
            browser.options.follow_redirect = False
            self.assertEqual(404, browser.open("/root/" + short_path))

    def test_traverse_to_content(self):
        IMarkManager(self.root).add_marker(IShortURLMarker)
        short_path = self.service.get_short_path(self.content)
        with self.layer.get_browser() as browser:
            browser.options.follow_redirect = False
            self.assertEqual(301, browser.open("/root/" + short_path))
            self.assertEqual(browser.headers['Location'],
                'http://localhost/root/folder/something')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TraversingTestCase))
    return suite
