# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok

from zope import component
from zope.cachedescriptors.property import CachedProperty
from zope.traversing.browser import absoluteURL

from Acquisition import aq_parent

from silva.core.views import views as silvaviews
from silva.core.interfaces import ISilvaObject, IContainer, IRoot
from zeam.form import silva as silvaforms
from silva.core.smi.settings import Settings

from .interfaces import IShortURLService, IShortURLMarker


class ShortURLInformation(silvaviews.Viewlet):
    grok.context(ISilvaObject)
    grok.order(100)
    grok.view(Settings)
    grok.viewletmanager(silvaforms.SMIFormPortlets)

    @CachedProperty
    def short_url_container(self):
        container = self.context
        while True:
            if IShortURLMarker.providedBy(container):
                return container
            if IRoot.providedBy(container):
                return None
            container = aq_parent(container)

    @CachedProperty
    def service(self):
        return component.queryUtility(IShortURLService)

    def available(self):
        return self.service is not None and \
            self.short_url_container is not None

    def update(self):
        short_path = self.service.get_short_path(self.context)
        self.short_url = absoluteURL(
            self.short_url_container, self.request) + '/' + short_path
