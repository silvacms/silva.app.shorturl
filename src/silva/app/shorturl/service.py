# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

import random
from copy import copy

from five import grok
from zope.intid.interfaces import IIntIds
from zope.component import getUtility, queryUtility, getMultiAdapter
from zope.interface import alsoProvides, noLongerProvides, Interface
from zope.location.interfaces import ISite
from zope import schema
from zope.cachedescriptors.property import Lazy

import BTrees

from Acquisition import aq_parent
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

from silva.core.interfaces.service import ISilvaLocalService
from silva.core.services.base import SilvaService
from silva.core.views.interfaces import IContentURL
from silva.app.forest.interfaces import IForestApplication
from silva.app.forest.interfaces import IForestWillBeDeactivatedEvent

from silva.translations import translate as _

from zeam.form import silva as silvaforms
from zeam.form.ztk.actions import EditAction

from .interfaces import IShortURLService, IShortURLApplication
from .interfaces import ICustomShortURLService
from .codec import ShortURLCodec


def closest_custom_short_url_service(location):
    while location:
        if ISite.providedBy(location):
            service = location._getOb('service_shorturls', None)
            if service is not None and \
                    ICustomShortURLService.providedBy(service):
                return service
        location = aq_parent(location)
    return None


def closest_site(location):
    while location:
        if ISite.providedBy(location):
            return location
        location = aq_parent(location)
    return None


BASE_ALPHABET = bytearray("abcdefghijkmnpqrstwxyzABCDEFGHIJKLMNPQRSTUVWXYZ")


def generate_alphabet():
    alphabet = copy(BASE_ALPHABET)
    random.shuffle(alphabet)
    return str(alphabet)


class CustomShortURLService(SilvaService):

    grok.baseclass()
    grok.implements(ICustomShortURLService)

    security = ClassSecurityInfo()
    family = BTrees.family32

    _custom_short_url_base = None

    manage_options = (
        {'label':'Settings', 'action':'manage_settings'},
        ) + SilvaService.manage_options

    def __init__(self, id):
        self._custom_url_index = self.family.OI.BTree()
        self._custom_url_reverse_index = self.family.IO.BTree()

    @Lazy
    def intids(self):
        return getUtility(IIntIds)

    security.declareProtected(
        'View Management Screens', 'register_custom_short_path')
    def register_custom_short_path(self, short_path, content):
        id = self.intids.register(content)
        try:
            old = self._custom_url_reverse_index[id]
            del self._custom_url_index[old]
            del self._custom_url_reverse_index[id]
        except KeyError:
            pass
        self._custom_url_index[short_path] = id
        self._custom_url_reverse_index[id] = short_path

    def unregister_custom_short_path(self, content):
        id = self.intids.register(content)
        try:
            old = self._custom_url_reverse_index[id]
            del self._custom_url_index[old]
            del self._custom_url_reverse_index[id]
        except KeyError:
            return False
        return True

    def get_custom_short_path(self, content):
        id = self.intids.register(content)
        try:
            return self._custom_url_reverse_index[id]
        except KeyError:
            return None

    def get_content_from_custom_short_path(self, short_path):
        try:
            id = self._custom_url_index[short_path]
        except KeyError:
            return None
        return self.intids.queryObject(id)

    def get_custom_short_url_base(self):
        return self._custom_short_url_base

    def get_custom_short_url(self, content, request):
        short_path = self.get_custom_short_path(content)
        if short_path is None: return None

        site = aq_parent(self)
        url_adapter = getMultiAdapter((site, request), IContentURL)
        host = self.get_custom_short_url_base()
        if host is not None:
            host = host.rstrip('/')
        url = url_adapter.url(host=host)
        return url.rstrip('/') + '/' + short_path

    security.declareProtected(
        'View Management Screens', 'set_custom_short_url_base')
    def set_custom_short_url_base(self, url):
        self._custom_short_url_base = url.rstrip().rstrip('/') + '/'


InitializeClass(CustomShortURLService)


class ShortURLLocalService(CustomShortURLService):
    """ Local service to store custom short URLs.
    """
    meta_type = 'Silva Short URL Site Local Service'

    grok.implements(ISilvaLocalService)
    grok.name('service_shorturls')


class ShortURLService(CustomShortURLService):
    """ Short URL Service.
    """
    grok.implements(IShortURLService)
    grok.name('service_shorturls')
    meta_type = 'Silva Short URL Service'

    security = ClassSecurityInfo()
    manage_options = (
        {'label':'Settings', 'action':'manage_settings'},
        ) + SilvaService.manage_options

    # silvaconf.icon('static/shorturl_service.png')

    _min_length = 4
    _block_size = 24
    _short_url_base = None

    def __init__(self, id):
        super(ShortURLService, self).__init__(id)
        self._alphabet = generate_alphabet()
        self._alphabet_set = set(self._alphabet)

    def get_short_url(self, content):
        base = self.get_short_url_base()
        if base is None:
            return None
        short_path = self.get_short_path(content)
        if short_path is None: return None
        return self.get_short_url_base() + short_path

    def get_short_url_base(self):
        return self._short_url_base

    security.declareProtected(
        'View Management Screens', 'set_short_url_base')
    def set_short_url_base(self, url):
        self._short_url_base = url.rstrip().rstrip('/') + '/'

    def _get_codec(self):
        return ShortURLCodec(alphabet=self._alphabet,
                             block_size=self._block_size)

    def get_silva_path(self):
        return self.get_root().getPhysicalPath()[1:]

    def get_short_path(self, content):
        codec = self._get_codec()
        intids = getUtility(IIntIds)
        id = intids.register(content)
        return codec.encode_url(id, min_length=self._min_length)

    def _get_int_id(self, short_path):
        codec = self._get_codec()
        return codec.decode_url(short_path)

    def get_content(self, short_path):
        content = self.get_content_from_custom_short_path(short_path)
        if content is not None:
            return content

        if self.validate_short_path(short_path):
            return self.get_content_from_short_path(short_path)

    def get_content_from_short_path(self, short_path):
        if not self.validate_short_path(short_path):
            return None
        id = self._get_int_id(short_path)
        intids = getUtility(IIntIds)
        return intids.queryObject(id)

    def validate_short_path(self, short_path):
        return not(set(short_path) - self._alphabet_set)

    security.declareProtected(
        'View Management Screens', 'is_active')
    def is_active(self):
        root = self.getPhysicalRoot()
        if IShortURLApplication.providedBy(root):
            path = getattr(root, '__silva__', tuple())
            if path == self.get_silva_path():
                return True
        return False

    security.declareProtected(
        'View Management Screens', 'activate')
    def activate(self):
        root = self.getPhysicalRoot()
        if not IForestApplication.providedBy(root):
            raise ValueError(
                _(u"silva.app.forest is not active."))
        if IShortURLApplication.providedBy(root):
            raise ValueError(
                _(u"The feature is already activated for a Silva site."))
        alsoProvides(root, IShortURLApplication)

    security.declareProtected(
        'View Management Screens', 'deactivate')
    def deactivate(self):
        root = self.getPhysicalRoot()
        noLongerProvides(root, IShortURLApplication)


InitializeClass(ShortURLService)


@grok.subscribe(IForestWillBeDeactivatedEvent)
def deactivate_shorturl_on_forest_deactivation(event):
    service = queryUtility(IShortURLService)
    if service is not None:
        service.deactivate()


class ShortURLServiceForm(silvaforms.ZMIComposedForm):
    grok.name('manage_settings')
    grok.context(ICustomShortURLService)

    label = _(u"Settings")
    description = _(u"Configure short URL traversing.")


class IShortURLSettingsFields(Interface):

    short_url_base = schema.TextLine(
        title=u"Base URL for short URLs")
    custom_short_url_base = schema.TextLine(
        title=u"Base URL for custom short URLs")


class ShortURLDomainSettings(silvaforms.ZMISubForm):
    grok.view(ShortURLServiceForm)
    grok.context(ICustomShortURLService)
    grok.order(10)

    label = _(u"Base URLs")
    description = _(u"Configure base URLS")

    ignoreContent = False
    ignoreRequest = True

    dataManager = silvaforms.SilvaDataManager
    fields = silvaforms.Fields(IShortURLSettingsFields)
    actions = silvaforms.Actions(EditAction('Save Changes'))

    fields['short_url_base'].available = \
        lambda f: IShortURLService.providedBy(f.context)


class ShortURLActivationSettings(silvaforms.ZMISubForm):
    """Activate the short url
    """
    grok.view(ShortURLServiceForm)
    grok.context(IShortURLService)
    grok.order(20)

    label = _(u'Activation')
    description = _(u"(De)Activate traversal on top level "
        "domain for automatic short urls")

    ignoreContent = False
    ignoreRequest = True

    @silvaforms.action(
        _(u"Activate"),
        available=lambda f: not f.context.is_active())
    def activate(self):
        try:
            self.context.activate()
            self.status = _(u'Activated.')
        except ValueError as error:
            self.status = error.args[0]
            return silvaforms.FAILURE
        return silvaforms.SUCCESS

    @silvaforms.action(
        _(u"Deactivate"),
        available=lambda f: f.context.is_active())
    def deactivate(self):
        try:
            self.context.deactivate()
            self.status = _(u'Deactivated.')
        except ValueError as error:
            self.status = error.args[0]
            return silvaforms.FAILURE
        return silvaforms.SUCCESS

