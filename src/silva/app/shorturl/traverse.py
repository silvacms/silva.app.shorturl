# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope import component
from zope.traversing.browser import absoluteURL
from zope.publisher.interfaces.browser import IBrowserRequest

from silva.core.views.traverser import SilvaPublishTraverse

from .interfaces import IShortURLMarker, IShortURLService


class ShortURLTraverser(SilvaPublishTraverse, grok.MultiAdapter):

    grok.adapts(IShortURLMarker, IBrowserRequest)
    grok.implements(IBrowserPublisher)

    def publishTraverse(self, request, name):
        service = component.queryUtility(IShortURLService)
        if service is not None:
            content = service.get_content(name)
            if content is not None:
                redirect_to = absoluteURL(content, request)
                request.response.redirect(redirect_to, status=301)
                return

        return super(ShortURLTraverser, self).publishTraverse(
            request, name)
