import unittest

from zope import component

from silva.core.layout.interfaces import IMarkManager
from silva.core.interfaces import IPublicationWorkflow
from silva.core.interfaces import IAccessSecurity

from silva.app.forest.interfaces import IForestService

from ..testing import FunctionalLayer
from ..interfaces import IShortURLMarker, IShortURLService


class TraversingTestCase(unittest.TestCase):

    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('folder', 'Folder')
        factory = self.root.folder.manage_addProduct['Silva']
        factory.manage_addMockupVersionedContent('something', 'Some Content')
        self.content = self.root.folder.something
        self.layer.login('manager')
        IPublicationWorkflow(self.content).publish()
        self.layer.logout()
        self.service = component.getUtility(IShortURLService)
        self.forest_service = component.getUtility(IForestService)
        self.forest_service.activate()
        self.service.activate()
        self.service.set_short_url_base('http://shorturl.local/')

    def test_traverse_with_short_url(self):
        short_path = self.service.get_short_path(self.content)
        with self.layer.get_browser() as browser:
            browser.set_request_header('X-VHM-URL', 'http://shorturl.local/')
            browser.options.follow_redirect = False
            self.assertEqual(301, browser.open("/" + short_path))
            self.assertEqual(browser.headers['location'],
                            'http://localhost/root/folder/something')

    def test_traverse_on_vhost(self):
        with self.layer.get_browser() as browser:
            browser.options.follow_redirect = False
            self.assertEqual(200, browser.open("/root/folder/something"))

    def test_traverse_on_private_object(self):
        access = component.getAdapter(self.root.folder, IAccessSecurity)
        access.set_minimum_role('Editor')

        short_path = self.service.get_short_path(self.content)
        with self.layer.get_browser() as browser:
            browser.set_request_header('X-VHM-URL', 'http://shorturl.local/')
            browser.options.follow_redirect = False
            self.assertEqual(301, browser.open("/" + short_path))
            self.assertEqual(browser.headers['location'],
                            'http://localhost/root/folder/something')
            browser.clear_request_headers()
            self.assertEqual(401, browser.open(browser.headers['location']))



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TraversingTestCase))
    return suite
