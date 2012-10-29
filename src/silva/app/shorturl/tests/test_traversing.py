import unittest

from zope import component

from silva.core.interfaces import IPublicationWorkflow
from silva.core.interfaces import IAccessSecurity

from silva.app.forest.interfaces import IForestService
from silva.core.interfaces import ISiteManager

from ..testing import FunctionalLayer
from ..interfaces import IShortURLService


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



class LocalSiteCustomURLTraversingTestCase(unittest.TestCase):

    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addPublication('pub', 'Local Site')
        factory = self.root.pub.manage_addProduct['Silva']
        factory.manage_addMockupVersionedContent('something', 'Some Content')
        self.content = self.root.pub.something
        self.layer.login('manager')
        IPublicationWorkflow(self.content).publish()
        ISiteManager(self.root.pub).make_site()
        factory = self.root.pub.manage_addProduct['silva.app.shorturl']
        factory.manage_addShortURLLocalService()
        local_service = self.root.pub.service_shorturls
        local_service.register_custom_short_path('ShortCut', self.content)
        self.layer.logout()

    def test_traverse_on_local_site_with_custom_short_path(self):
        """ Test traversing on the publication (local site) using a
        custom short path.
        """
        with self.layer.get_browser() as browser:
            browser.options.follow_redirect = False
            self.assertEqual(301,
                browser.open('http://localhost/root/pub/ShortCut'))
            self.assertEqual(browser.headers['location'],
                'http://localhost/root/pub/something')


    def test_traverse_to_content(self):
        """ Normal traversing should continue to work.
        """
        with self.layer.get_browser() as browser:
            browser.options.follow_redirect = False
            self.assertEqual(200,
                browser.open('http://localhost/root/pub/something'))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TraversingTestCase))
    suite.addTest(unittest.makeSuite(LocalSiteCustomURLTraversingTestCase))
    return suite
