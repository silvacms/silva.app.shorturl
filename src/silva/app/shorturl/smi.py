# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok

from zope.interface import Interface
from zope import component
from zope import schema
from zope.cachedescriptors.property import Lazy
from zope.location.interfaces import ISite
from zope.traversing.browser import absoluteURL
from zope.app.container.interfaces import INameChooser

from silva.core.views import views as silvaviews
from silva.core.interfaces import ISilvaObject, ContentError
from zeam.form import silva as silvaforms
from silva.core.smi.settings import Settings
from silva.translations import translate as _

from .interfaces import IShortURLService
from .service import closest_custom_short_url_service, closest_site


class ShortURLInformation(silvaviews.Viewlet):
    grok.context(ISilvaObject)
    grok.order(100)
    grok.view(Settings)
    grok.viewletmanager(silvaforms.SMIFormPortlets)

    @Lazy
    def service(self):
        return component.queryUtility(IShortURLService)

    @Lazy
    def custom_short_url_service(self):
        return closest_custom_short_url_service(self.context)

    def available(self):
        return self.service is not None

    def update(self):
        if not self.available():
            return
        self.short_url = (self.service.get_short_url_base() or '') + \
            self.service.get_short_path(self.context)
        custom_short_path = self.custom_short_url_service.get_custom_short_path(
            self.context)
        self.custom_short_url = None
        if custom_short_path is not None:
            self.custom_short_url = absoluteURL(
                closest_site(self.custom_short_url_service),
                self.request).rstrip('/') + '/' + custom_short_path


class ShortURLFields(Interface):
    custom_path = schema.TextLine(title=_(u"Custom short path"),
                                  required=True)


def validate_custom_path(value, form):
    if value is silvaforms.NO_VALUE:
        return _(u'Missing required value.')
    try:
        service = closest_custom_short_url_service(form.context)
        site = closest_site(service)
        INameChooser(site).checkName(value, None)
    except ContentError as e:
        return e.reason
    return None


class ShortURLForm(silvaforms.SMISubForm):

    label = _(u'Short URL')

    grok.view(Settings)
    grok.context(ISilvaObject)
    grok.order(100)
    fields = silvaforms.Fields(ShortURLFields)

    ignoreContent = True
    ignoreRequest = True

    @Lazy
    def site(self):
        if self.custom_short_url_service is not None:
            return closest_site(self.custom_short_url_service)

    def custom_short_path_default(self):
        return self.custom_short_url_service.get_custom_short_path(
            self.context) or silvaforms.NO_VALUE

    fields['custom_path'].validate = validate_custom_path
    fields['custom_path'].defaultValue = custom_short_path_default

    def available(self):
        return self.custom_short_url_service is not None \
            and not ISite.providedBy(self.context)

    @Lazy
    def custom_short_url_service(self):
        return closest_custom_short_url_service(self.context)

    @silvaforms.action(title=_(u"Clear custom path"), htmlAttributes={
        'data-confirmation': _(u'Are you sure you want to clear'
                                ' the custom short path ?')})
    def clear_custom_path(self):
        self.custom_short_url_service.unregister_custom_short_path(
            self.context)
        return silvaforms.SUCCESS

    @silvaforms.action(title=_(u"Save custom path"))
    def save_custom_path(self):
        data, errors = self.extractData()
        if errors:
            return silvaforms.FAILURE
        self.custom_short_url_service.register_custom_short_path(
            data.get('custom_path'), self.context)
        return silvaforms.SUCCESS
