import unittest

from zope import component

from silva.app.forest.interfaces import IForestService
from silva.app.forest.service import VirtualHost, Rewrite

from silva.core.interfaces import IAccessSecurity
from silva.core.interfaces import IPublicationWorkflow
from silva.core.interfaces import ISiteManager

from ..testing import FunctionalLayer
from ..interfaces import IShortURLService

# XXX: add test with SilvaLayer


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
        self.service = component.getUtility(IShortURLService)
        self.service.register_custom_short_path('ShortCut', self.content)
        self.layer.logout()

    def test_traverse_to_content(self):
        """ Normal traversing should continue to work.
        """
        with self.layer.get_browser() as browser:
            browser.options.handle_errors = False
            browser.options.follow_redirect = False
            self.assertEqual(200,
                browser.open('http://localhost/root/folder/something'))

    def test_traverse_with_short_url(self):
        short_path = self.service.get_short_path(self.content)
        with self.layer.get_browser() as browser:
            browser.options.handle_errors = False
            browser.options.follow_redirect = False
            self.assertEqual(301, browser.open("/root/$" + short_path))
            self.assertEqual(browser.headers['location'],
                            'http://localhost/root/folder/something')

    def test_traverse_on_default(self):
        """ Traversing on default redirects to container
        """
        self.layer.login('manager')
        factory = self.root.folder.manage_addProduct['Silva']
        factory.manage_addMockupVersionedContent('index', 'Some Content')
        index = self.root.folder.index
        self.assertTrue(index)
        IPublicationWorkflow(index).publish()
        short_path = self.service.get_short_path(index)
        self.layer.logout()
        with self.layer.get_browser() as browser:
            browser.options.handle_errors = False
            browser.options.follow_redirect = False
            self.assertEqual(301, browser.open("/root/$" + short_path))
            self.assertEqual(browser.headers['location'],
                            'http://localhost/root/folder')

    def test_traverse_with_custom_short_path(self):
        with self.layer.get_browser() as browser:
            browser.options.handle_errors = False
            browser.options.follow_redirect = False
            self.assertEqual(301, browser.open("/root/ShortCut"))
            self.assertEqual(browser.headers['location'],
                            'http://localhost/root/folder/something')

    def test_traverse_on_private_object(self):
        access = component.getAdapter(self.root.folder, IAccessSecurity)
        access.set_minimum_role('Editor')

        short_path = self.service.get_short_path(self.content)
        with self.layer.get_browser() as browser:
            browser.options.handle_errors = False
            browser.options.follow_redirect = False
            self.assertEqual(301, browser.open("/root/$" + short_path))
            self.assertEqual(browser.headers['location'],
                            'http://localhost/root/folder/something')
            browser.clear_request_headers()
            self.assertEqual(401, browser.open(browser.headers['location']))

    def test_traverse_with_short_url_with_forest(self):
        forest_service = component.getUtility(IForestService)
        forest_service.activate()
        forest_service.set_hosts(
            [VirtualHost(
                'http://infrae.com/',
                [],
                [Rewrite('/', '/root', None)])])
        short_path = self.service.get_short_path(self.content)
        with self.layer.get_browser() as browser:
            browser.options.handle_errors = False
            browser.options.follow_redirect = False
            browser.set_request_header('X-VHM-URL', 'http://infrae.com/')
            self.assertEqual(301, browser.open("/$" + short_path))
            self.assertEqual(browser.headers['location'],
                            'http://infrae.com/folder/something')

    def test_custom_path_with_forest(self):
        forest_service = component.getUtility(IForestService)
        forest_service.activate()
        forest_service.set_hosts(
            [VirtualHost(
                'http://infr.ae/',
                [],
                [Rewrite('/', '/root', None)]),
             VirtualHost(
                'http://infrae.com/',
                [],
                [Rewrite('/', '/root', None)])]
            )

        self.service.set_rewrite_url_base('http://infrae.com/')
        with self.layer.get_browser() as browser:
            browser.options.handle_errors = False
            browser.options.follow_redirect = False
            browser.set_request_header('X-VHM-URL', 'http://infr.ae/')
            self.assertEqual(301, browser.open("/ShortCut"))
            self.assertEqual(browser.headers['location'],
                            'http://infrae.com/folder/something')


class LocalSiteURLTraversingTestCase(unittest.TestCase):

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
        factory.manage_addShortURLService()
        self.local_service = self.root.pub.service_shorturls
        self.local_service.register_custom_short_path('ShortCut', self.content)
        self.layer.logout()

    def test_traverse_on_local_site_with_custom_short_path(self):
        """ Test traversing on the publication (local site) using a
        custom short path.
        """
        with self.layer.get_browser() as browser:
            browser.options.handle_errors = False
            browser.options.follow_redirect = False
            self.assertEqual(301,
                browser.open('http://localhost/root/pub/ShortCut'))
            self.assertEqual(browser.headers['location'],
                'http://localhost/root/pub/something')

    def test_traverse_to_content(self):
        """ Normal traversing should continue to work.
        """
        with self.layer.get_browser() as browser:
            browser.options.handle_errors = False
            browser.options.follow_redirect = False
            self.assertEqual(200,
                browser.open('http://localhost/root/pub/something'))

    def test_custom_path_with_forest(self):
        forest_service = component.getUtility(IForestService)
        forest_service.activate()
        forest_service.set_hosts(
            [VirtualHost(
                'http://infr.ae/',
                [],
                [Rewrite('/', '/root/pub', None)]),
             VirtualHost(
                'http://infrae.com/',
                [],
                [Rewrite('/', '/root/pub', None)])]
            )

        self.local_service.set_rewrite_url_base('http://infrae.com/')
        with self.layer.get_browser() as browser:
            browser.options.handle_errors = False
            browser.options.follow_redirect = False
            browser.set_request_header('X-VHM-URL', 'http://infr.ae/')
            self.assertEqual(301, browser.open("/ShortCut"))
            self.assertEqual(browser.headers['location'],
                            'http://infrae.com/something')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TraversingTestCase))
    suite.addTest(unittest.makeSuite(LocalSiteURLTraversingTestCase))
    return suite
