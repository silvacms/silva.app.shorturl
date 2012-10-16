# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

import random
from copy import copy

from five import grok
from zope.intid.interfaces import IIntIds
from zope.component import getUtility

import BTrees

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

from silva.core.services.base import SilvaService

from .interfaces import IShortURLService
from .codec import ShortURLCodec



BASE_ALPHABET = bytearray("abcdefghijkmnpqrstwxyzABCDEFGHIJKLMNPQRSTUVWXYZ")


def generate_alphabet():
    alphabet = copy(BASE_ALPHABET)
    random.shuffle(alphabet)
    return str(alphabet)


class ShortURLService(SilvaService):
    grok.implements(IShortURLService)
    grok.name('service_shorturl')
    meta_type = 'Silva Shorl URL Service'

    security = ClassSecurityInfo()
    family = BTrees.family32

    # silvaconf.icon('static/shorturl_service.png')

    _min_length = 4
    _block_size = 24

    def __init__(self, id):
        super(ShortURLService, self).__init__(id)
        self._alphabet = generate_alphabet()
        self._alphabet_set = set(self._alphabet)
        self._custom_url_index = self.family.OI.BTree()
        self._custom_url_reverse_index = self.family.IO.BTree()

    def _get_codec(self):
        return ShortURLCodec(alphabet=self._alphabet,
                             block_size=self._block_size)

    def get_short_path(self, content):
        codec = self._get_codec()
        intids = getUtility(IIntIds)
        id = intids.register(content)
        return codec.encode_url(id, min_length=self._min_length)

    def _get_int_id(self, short_path):
        codec = self._get_codec()
        return codec.decode_url(short_path)

    def get_content(self, short_path):
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

    def get_registered_short_path(self, content):
        intids = getUtility(IIntIds)
        id = intids.register(content)
        return self._custom_url_reverse_index[id]

    def get_content_from_custom_short_path(self, short_path):
        id = self._custom_url_index[short_path]
        if id is not None:
            intids = getUtility(IIntIds)
            return intids.queryObject(id)

    def validate_short_path(self, short_path):
        return not(set(short_path) - self._alphabet_set)


InitializeClass(ShortURLService)