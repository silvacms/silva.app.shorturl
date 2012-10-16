# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok

from zope import component

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

    def get_service(self):
        return component.queryUtility(IShortURLService)

    def available(self):
        return self.get_service() is not None

    def update(self):
        service = self.get_service()
        self.short_path = service.get_short_path(self.context)
