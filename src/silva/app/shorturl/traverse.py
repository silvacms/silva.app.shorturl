# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope import component
from zope.traversing.browser import absoluteURL

from infrae.wsgi.interfaces import IRequest, ITraverser
from infrae.wsgi.utils import traverse

from silva.app.forest.virtualhosting import VirtualHosting

from .interfaces import IShortURLService, IShortURLApplication

from zExceptions import NotFound, BadRequest
from ZPublisher.BaseRequest import UNSPECIFIED_ROLES
from ZPublisher.BaseRequest import quote

from Acquisition import aq_chain


class ShortURLRoot(object):

    def __init__(self, root):
        self.root = root


class Redirect(object):

    def __init__(self, content, request):
        self.content = content
        self.request = request

    def __call__(self):
        url = absoluteURL(self.content, self.request)
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
        content = service.get_content(path.pop())
        if content is not None:
            view = Redirect(content, self.request)
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
            if service.get_short_url_base() == url.rstrip('/') + '/':
                return ShortURLRoot(root), method, path

        return super(ShortURLVirtualHosting, self).__call__(method, path)
