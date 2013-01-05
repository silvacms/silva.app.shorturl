# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

import random
from copy import copy

from five import grok
from zope.intid.interfaces import IIntIds
from zope.component import getUtility, getMultiAdapter
from zope.interface import Interface
from zope.location.interfaces import ISite
from zope import schema
from zope.cachedescriptors.property import Lazy

import BTrees

from Acquisition import aq_parent
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

from silva.core import conf as silvaconf
from silva.core.interfaces import ISilvaNameChooser, ContentError
from silva.core.interfaces import IInvisibleService
from silva.core.interfaces.service import ISilvaLocalService
from silva.core.services.base import SilvaService
from silva.core.views.interfaces import IContentURL

from silva.translations import translate as _

from zeam.form import silva as silvaforms
from zeam.form.ztk.actions import EditAction

from .interfaces import IShortURLService, IShortURLResolverService
from .codec import ShortURLCodec

from . import SERVICE_NAME, SHORT_URL_PREFIX


def closest_short_url_service(location):
    while location:
        if ISite.providedBy(location):
            service = location._getOb(SERVICE_NAME, None)
            if service is not None and \
                    IShortURLService.providedBy(service):
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


class ShortURLService(SilvaService):
    """ Short url service.
    """
    grok.name(SERVICE_NAME)
    grok.implements(IShortURLService, ISilvaLocalService)
    silvaconf.icon('static/%s.png' % SERVICE_NAME)

    meta_type = 'Short URL Service'

    security = ClassSecurityInfo()
    family = BTrees.family32

    _short_url_base = None
    _rewrite_url_base = None

    manage_options = (
        {'label':'Short URL Configuration', 'action':'manage_settings'},
    ) + SilvaService.manage_options

    def __init__(self, id):
        super(ShortURLService, self).__init__(id)
        self._custom_url_index = self.family.OI.BTree()
        self._custom_url_reverse_index = self.family.IO.BTree()

    @Lazy
    def _resolver(self):
        return getUtility(IShortURLResolverService)

    @Lazy
    def intids(self):
        return getUtility(IIntIds)

    # shortcuts for resolver

    def get_content(self, short_path):
        return self._resolver.get_content(short_path)

    def get_short_path(self, content):
        return self._resolver.get_short_path(content)

    def validate_short_path(self, short_path):
        return self._resolver.validate_short_path(short_path)

    # --

    security.declareProtected(
        'View Management Screens', 'register_custom_short_path')
    def register_custom_short_path(self, short_path, content):
        id = self.intids.register(content)
        short_path_set = self._custom_url_reverse_index.get(id, None)
        if short_path_set is None:
            self._custom_url_reverse_index[id] = \
                short_path_set = self.family.OO.Set()
        short_path_set.add(short_path)
        self._custom_url_index[short_path] = id

    def unregister_custom_short_path(self, short_path, content):
        id = self.intids.register(content)
        short_path_set = self._custom_url_reverse_index.get(id, None)
        if short_path_set is None:
            return False
        short_path_set.remove(short_path)
        if not short_path_set:
            del self._custom_url_reverse_index[id]
        del self._custom_url_index[short_path]
        return True

    def get_custom_short_paths(self, content):
        id = self.intids.register(content)
        try:
            return set(self._custom_url_reverse_index[id])
        except KeyError:
            return set()

    def get_content_from_custom_short_path(self, short_path):
        try:
            id = self._custom_url_index[short_path]
        except KeyError:
            return None
        return self.intids.queryObject(id)

    def get_short_url(self, content, request):
        short_path = self.get_short_path(content)
        if short_path is None:
            return None
        site = aq_parent(self)
        url_adapter = getMultiAdapter((site, request), IContentURL)
        url = url_adapter.url(host=self.get_short_url_base())
        return url.rstrip('/') + '/' + SHORT_URL_PREFIX + short_path

    def get_short_url_base(self):
        return self._short_url_base

    def get_prefix_url(self, request):
        site = self.get_container()
        url_adapter = getMultiAdapter((site, request), IContentURL)
        url = url_adapter.url(host=self.get_short_url_base())
        return url.rstrip('/') + '/'

    security.declareProtected(
        'View Management Screens', 'set_short_url_base')
    def set_short_url_base(self, url):
        if url:
            self._short_url_base = url.rstrip().rstrip('/')
        else:
            self._short_url_base = None

    def get_rewrite_url_base(self):
        return self._rewrite_url_base

    security.declareProtected(
        'View Management Screens', 'set_rewrite_url_base')
    def set_rewrite_url_base(self, url):
        if url:
            self._rewrite_url_base = url.rstrip().rstrip('/')
        else:
            self._rewrite_url_base = None

InitializeClass(ShortURLService)


class CustomURLNameChooser(grok.Subscription):
    grok.implements(ISilvaNameChooser)
    grok.context(ISite)
    grok.order(10000)

    def __init__(self, context):
        self.context = context

    def checkName(self, name, content):
        service = self.context._getOb(SERVICE_NAME, None)
        if service is not None and IShortURLService.providedBy(service):
            content = service.get_content_from_custom_short_path(name)
            if content is not None:
                raise ContentError(
                    _(u"A custom short URL `${name}` already exists.",
                        mapping=dict(name=name)), self.context)

    def chooseName(self, name, content, **kw):
        return name


class ShortURLResolverService(SilvaService):
    """ Service for resolving short urls.
    """
    grok.implements(IShortURLResolverService, IInvisibleService)
    grok.name('service_shorturls_resolver')

    meta_type = 'Silva Short URL Resolver'

    security = ClassSecurityInfo()
    silvaconf.icon('static/%s.png' % SERVICE_NAME)

    _min_length = 4
    _block_size = 24

    def __init__(self, id):
        super(ShortURLResolverService, self).__init__(id)
        self._alphabet = generate_alphabet()
        self._alphabet_set = set(self._alphabet)

    def get_short_url_target_host(self):
        return self._short_url_target_host

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
        if short_path:
            return not(set(short_path) - self._alphabet_set)
        return False


InitializeClass(ShortURLResolverService)


class ShortURLServiceForm(silvaforms.ZMIComposedForm):
    grok.name('manage_settings')
    grok.context(IShortURLService)

    label = _(u"Short URL Service")
    description = _(u"Configure Short URL traversing and/or redirection.")


class IShortURLSettingsFields(Interface):

    short_url_base = schema.TextLine(
        title=u"Base domain for Short URLs",
        description=u"This is an optional field. If nothing is filled in then Short URLs will have the same domain as your site's public pages. However if you've created a special domain for Short URLs (e.g. http://s.yoursite.com) you can fill it in here.",
        required=False)
    rewrite_url_base = schema.TextLine(
        title=u"Landing domain to redirect to",
        description=u"If you're using a special base domain you can have incoming Short URL requests get redirected to a normal landing domain (e.g. http://yourlongsitename.com).",
        required=False)


class ShortURLDomainSettings(silvaforms.ZMISubForm):
    grok.view(ShortURLServiceForm)
    grok.context(IShortURLService)
    grok.order(10)

    label = _(u"Domain settings")
    description = _(u"Change the base and landing domains for Short URLs.")

    ignoreContent = False
    ignoreRequest = True

    dataManager = silvaforms.SilvaDataManager
    fields = silvaforms.Fields(IShortURLSettingsFields)
    actions = silvaforms.Actions(EditAction('Save Changes'))
