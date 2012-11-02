# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt


from silva.core.interfaces import ISilvaService
from silva.app.forest.interfaces import IForestApplication


class ICustomShortURLService(ISilvaService):

    def register_custom_short_path(short_path, content):
        """ Register a custom short path for content.
        """

    def get_custom_short_path(content):
        """ Retrieve custom short path from content.
        """

    def get_content_from_custom_short_path(short_path):
        """ Retrieve content from custom short path.
        """

    def get_custom_short_url(content, request):
        """ Retrieve the custom short url for the content.
        """

    def get_custom_short_url_base():
        """ Retrieve the base URL for custom URLs
        """

    def set_custom_short_url_base(url):
        """ Set the custom short URL base.
        """


class IShortURLService(ICustomShortURLService):

    def get_content(short_path):
        """ Return  for silva object.
        """

    def get_content_from_short_path(short_path):
        """ Retrieve content from short path. 
        """

    def get_short_url(content):
        """ Retrieve short url for content.
        """

    def get_short_url_base():
        """ Get the base URL for short URLs.
        """

    def set_short_url_base(url):
        """ Set the base URL for short URLs.
        """

    def get_short_path(content):
        """ Get content's short path.
        """

    def validate_short_path(short_path):
        """ Tell if the short path is valid.
        """

    def is_active():
        """ Tell if the service is active.
        """

    def activate():
        """ Activate the service.
        """

    def deactivate():
        """ Deactivate the service.
        """


class IShortURLApplication(IForestApplication):
    """ Marker for zope site to allow short URL traversing.
    """
