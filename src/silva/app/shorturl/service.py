# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

import random
from copy import copy

from five import grok
from zope.intid.interfaces import IIntIds
from zope.component import getUtility, queryUtility
from zope.interface import alsoProvides, noLongerProvides, Interface
from zope import schema

import BTrees

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

from silva.core.services.base import SilvaService
from silva.app.forest.interfaces import IForestApplication
from silva.app.forest.interfaces import IForestWillBeDeactivatedEvent

from silva.translations import translate as _

from zeam.form import silva as silvaforms
from zeam.form.ztk.actions import EditAction

from .interfaces import IShortURLService, IShortURLApplication
from .codec import ShortURLCodec


BASE_ALPHABET = bytearray("abcdefghijkmnpqrstwxyzABCDEFGHIJKLMNPQRSTUVWXYZ")


def generate_alphabet():
    alphabet = copy(BASE_ALPHABET)
    random.shuffle(alphabet)
    return str(alphabet)


class ShortURLService(SilvaService):
    grok.implements(IShortURLService)
    grok.name('service_shorturls')
    meta_type = 'Silva Shorl URL Service'

    security = ClassSecurityInfo()
    manage_options = (
        {'label':'Settings', 'action':'manage_settings'},
        ) + SilvaService.manage_options

    family = BTrees.family32

    # silvaconf.icon('static/shorturl_service.png')

    _min_length = 4
    _block_size = 24
    _short_url_base = None

    def __init__(self, id):
        super(ShortURLService, self).__init__(id)
        self._alphabet = generate_alphabet()
        self._alphabet_set = set(self._alphabet)
        self._custom_url_index = self.family.OI.BTree()
        self._custom_url_reverse_index = self.family.IO.BTree()
        self._short_url_base = None

    def _get_codec(self):
        return ShortURLCodec(alphabet=self._alphabet,
                             block_size=self._block_size)

    def get_short_url_base(self):
        return self._short_url_base

    security.declareProtected(
    'View Management Screens', 'set_short_url_base')
    def set_short_url_base(self, url):
        self._short_url_base = url.rstrip().rstrip('/') + '/'

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
        if content is None:
            if self.validate_short_path(short_path):
                return self.get_content_from_short_path(short_path)

    def get_content_from_short_path(self, short_path):
        if not self.validate_short_path(short_path):
            return None
        id = self._get_int_id(short_path)
        intids = getUtility(IIntIds)
        return intids.queryObject(id)

    def register_custom_short_path(self, short_path, content):
        intids = getUtility(IIntIds)
        id = intids.register(content)
        self._custom_url_index[short_path] = id
        self._custom_url_reverse_index[id] = short_path

    def get_custom_short_path(self, content):
        intids = getUtility(IIntIds)
        id = intids.register(content)
        try:
            return self._custom_url_reverse_index[id]
        except KeyError:
            return None

    def get_content_from_custom_short_path(self, short_path):
        try:
            id = self._custom_url_index[short_path]
        except KeyError:
            return None
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


class IShortURLSettingsFields(Interface):

    short_url_base = schema.TextLine(title=u"Base URL for short URLs")


class ShortURLActivationSettings(silvaforms.ZMIForm):
    """Activate the short url
    """
    grok.name('manage_settings')
    grok.context(IShortURLService)
    grok.order(10)

    ignoreContent = False
    ignoreRequest = True

    dataManager = silvaforms.SilvaDataManager

    fields = silvaforms.Fields(IShortURLSettingsFields)
    label = _(u"Settings")
    description = _(u"Configure and activate short url traversing.")

    actions = silvaforms.Actions(EditAction('Save'))

    @silvaforms.action(
        _(u"Activate"),
        available=lambda f: not f.context.is_active())
    def activate(self):
        try:
            self.context.activate()
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
        except ValueError as error:
            self.status = error.args[0]
            return silvaforms.FAILURE
        return silvaforms.SUCCESS

