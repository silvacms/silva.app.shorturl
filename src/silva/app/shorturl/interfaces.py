# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt


from zope.interface import Interface
from silva.core.interfaces import ISilvaService
from silva.app.forest.interfaces import IForestApplication


class IShortURLResolver(Interface):

    def get_content(short_path):
        """ Retrieve content from short path. 
        """

    def get_short_path(content):
        """ Get content's short path.
        """

    def validate_short_path(short_path):
        """ Tell if the short path is valid.
        """


class IShortURLResolverService(ISilvaService, IShortURLResolver):
    """ Service from resolving short urls.
    """


class IShortURLService(ISilvaService):

    def register_custom_short_path(short_path, content):
        """ Register a custom short path for content.
        """

    def get_custom_short_paths(content):
        """ Retrieve custom short paths for the content.
        """

    def get_content_from_custom_short_path(short_path):
        """ Retrieve content from custom short path.
        """

    def get_prefix_url(request):
        """ Retrieve the base of short urls after computation (forest, local site).
        """

    def get_short_url_base():
        """ Get the base URL for short URLs.
        """

    def set_short_url_base(url):
        """ Set the base URL for short URLs.
        """


class IShortURLApplication(IForestApplication):
    """ Marker for zope site to allow short URL traversing.
    """
