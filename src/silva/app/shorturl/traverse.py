# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope import component
from zope.publisher.interfaces.browser import IBrowserRequest

from silva.core.layout.traverser import SkinnyTraverser
from zope.location.interfaces import ISite

from silva.core.views.interfaces import IContentURL

from .interfaces import IShortURLService
from . import SERVICE_NAME, SHORT_URL_PREFIX


class ShortURLRoot(object):

    def __init__(self, root):
        self.root = root


class Redirect(object):

    __parent__ = None
    __name__ = None

    def __init__(self, content, request, parent, name, host=None):
        self.content = content
        self.request = request
        self.host = host
        self.__parent__ = parent
        self.__name__ = name

    def __call__(self):
        url_adapter = component.getMultiAdapter(
            (self.content, self.request), IContentURL)
        url = url_adapter.url(host=self.host)
        self.request.response.redirect(url, status=301)
        return ''


class ShortURLSitePublishTraverse(SkinnyTraverser, grok.MultiAdapter):
    """ Override silva traverser for site.
    """
    grok.adapts(ISite, IBrowserRequest)

    def publishTraverse(self, request, name):
        service = self.context._getOb(SERVICE_NAME, None)
        if service is None or not IShortURLService.providedBy(service):
            return super(ShortURLSitePublishTraverse, self).publishTraverse(
                request, name)

        if name.startswith(SHORT_URL_PREFIX):
            short_path = name[1:]
            if service.validate_short_path(short_path):
                content = service.get_content(short_path)
                if content is not None:
                    return Redirect(content, self.request, self.context, name,
                        host=service.get_rewrite_url_base())
        else:
            content = service.get_content_from_custom_short_path(name)
            if content is not None:
                return Redirect(content, self.request, self.context, name,
                    host=service.get_rewrite_url_base())

        return super(ShortURLSitePublishTraverse, self).publishTraverse(
                request, name)
