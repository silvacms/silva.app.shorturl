# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

from zope.interface import Interface

from silva.core.interfaces import ISilvaService
from silva.core.layout.interfaces import ICustomizableMarker


class IShortURLService(ISilvaService):

    def get_min_length(self):
        """ Minimum length for short URLS.
        """

    def get_block_size(self):
        """ Block size.
        """

    def get_short_url(self, content):
        """ Return short url for silva object.
        """


class IShortURLMarker(ICustomizableMarker):
    """ Allow traversing to object through short URL.
    """
