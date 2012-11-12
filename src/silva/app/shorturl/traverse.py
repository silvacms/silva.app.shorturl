# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope import component
from zope.publisher.interfaces.browser import IBrowserRequest

from infrae.wsgi.interfaces import IRequest, ITraverser
from infrae.wsgi.utils import traverse

from silva.app.forest.virtualhosting import VirtualHosting
from silva.core.layout.traverser import SkinnyTraverser
from zope.location.interfaces import ISite

from silva.core.views.interfaces import IContentURL
from silva.core.interfaces.errors import ContentError
from silva.translations import translate as _
from Products.Silva.mangle import SilvaNameChooser

from .interfaces import IShortURLService, IShortURLApplication
from .interfaces import ICustomShortURLService

from zExceptions import NotFound, BadRequest
from ZPublisher.BaseRequest import UNSPECIFIED_ROLES
from ZPublisher.BaseRequest import quote

from Acquisition import aq_chain


class ShortURLRoot(object):

    def __init__(self, root):
        self.root = root


class Redirect(object):

    __parent__ = None
    __name__ = None

    def __init__(self, content, request, host=None):
        self.content = content
        self.request = request
        self.host = host

    def __call__(self):
        url_adapter = component.getMultiAdapter(
            (self.content, self.request), IContentURL)
        url = url_adapter.url(host=self.host)
        self.request.response.redirect(url, status=301)
        return ''


class Traverser(grok.MultiAdapter):
    grok.adapts(ShortURLRoot, IRequest)
    grok.implements(ITraverser)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, method, path):
        if len(path) != 1:
            raise NotFound()
        root = self.context.root
        silva_root = traverse(root.__silva__, root, request=self.request)
        service = component.getUtility(IShortURLService)
        path_component = path.pop()
        content = service.get_content(path_component)
        if content is not None:
            view = Redirect(content, self.request,
                host=service.get_short_url_target_host())
            view.__parent__ = self.context
            view.__name__ = path_component
            chain = aq_chain(content)
            parents = chain[:chain.index(silva_root) + 1]
            self.request.roles = UNSPECIFIED_ROLES
            self.request.steps = map(
                lambda x: quote(x.id), reversed(parents)) + ['@@index.html']
            self.request['PARENTS'] = parents
            self.request['PUBLISHED'] = view
            return view
        raise NotFound()


class ShortURLVirtualHosting(VirtualHosting):
    grok.adapts(IShortURLApplication, IRequest)

    def __call__(self, method, path):
        url = self.request.environ.get('HTTP_X_VHM_URL', '')
        root = self.context
        service = None
        try:
            service = traverse(root.__silva__ + ('service_shorturls',), root)
        except BadRequest:
            pass
        if service is not None:
            if service.get_short_url_base() == url.rstrip('/'):
                return ShortURLRoot(root), method, path

        return super(ShortURLVirtualHosting, self).__call__(method, path)


class ShortURLNameChooser(SilvaNameChooser):
    """ Prevent creating objects that collide with custom short URLs.
    """
    grok.context(ISite)

    def checkName(self, name, content):
        service = self.container._getOb('service_shorturls', None)
        if service is not None and ICustomShortURLService.providedBy(service):
            content = service.get_content_from_custom_short_path(name)
            if content is not None:
                raise ContentError(
                    _(u"A custom short URL `${name}` already exists.",
                        mapping=dict(name=name)), self.container)
        return super(ShortURLNameChooser, self)


class ShortURLSitePublishTraverse(SkinnyTraverser, grok.MultiAdapter):
    """ Override silva traverser for site.
    """
    grok.adapts(ISite, IBrowserRequest)

    def publishTraverse(self, request, name):
        service = self.context._getOb('service_shorturls', None)
        if service is not None and ICustomShortURLService.providedBy(service):
            content = service.get_content_from_custom_short_path(name)
            if content is not None:
                view = Redirect(content, self.request,
                    host=service.get_custom_short_url_base())
                view.__parent__ = self.context
                view.__name__ = name
                return view
        return super(
            ShortURLSitePublishTraverse, self).publishTraverse(request, name)
