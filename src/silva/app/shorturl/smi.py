# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok

from zope import component
from zope.cachedescriptors.property import CachedProperty

from silva.core.views import views as silvaviews
from silva.core.interfaces import ISilvaObject
from zeam.form import silva as silvaforms
from silva.core.smi.settings import Settings

from .interfaces import IShortURLService


class ShortURLInformation(silvaviews.Viewlet):
    grok.context(ISilvaObject)
    grok.order(100)
    grok.view(Settings)
    grok.viewletmanager(silvaforms.SMIFormPortlets)

    @CachedProperty
    def service(self):
        return component.queryUtility(IShortURLService)

    def available(self):
        return self.service is not None and self.service.is_active()

    def update(self):
        self.short_url = self.service.get_short_url_base() + \
            self.service.get_short_path(self.context)
        custom_short_path = self.service.get_custom_short_path(self.context)
        self.custom_short_url = None
        if custom_short_path is not None:
            self.custom_short_url = self.service.get_short_url_base() + \
                custom_short_path
