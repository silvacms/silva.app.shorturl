# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok

from zope import component
from zope import schema
from zope.app.container.interfaces import INameChooser
from zope.cachedescriptors.property import Lazy
from zope.interface import Interface
from zope.intid.interfaces import IIntIds
from zope.location.interfaces import ISite
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.traversing.browser import absoluteURL

from silva.core import conf as silvaconf
from silva.core.interfaces import ISilvaObject, ContentError
from silva.core.interfaces.adapters import IIconResolver
from silva.core.smi.settings import Settings
from silva.core.views import views as silvaviews
from silva.fanstatic import need
from silva.translations import translate as _
from silva.ui.rest import UIREST
from zeam.form import silva as silvaforms
from zeam.form.base.widgets import FieldWidget
from zeam.form.ztk.widgets.textline import TextLineField

from .interfaces import IShortURLService, ICustomShortURLService
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
        self.short_url = None
        self.custom_short_url = None

        if self.service.is_active():
            self.short_url = self.service.get_short_url(self.context)

        if self.custom_short_url_service is not None:
            self.custom_short_url = \
                self.custom_short_url_service.get_custom_short_url(
                    self.context,
                    self.request)


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


class RESTCustomShortPathInfo(UIREST):
    grok.context(ICustomShortURLService)
    grok.require('silva.ReadSilvaContent')
    grok.name('silva.app.shorturl.custom_path_lookup')

    def GET(self, custom_path):
        content = self.context.get_content_from_custom_short_path(custom_path)
        if content is None:
            return self.json_response(None)
        int_id = component.getUtility(IIntIds).register(content)
        return self.json_response({
            'id': content.getId(),
            'intid': int_id,
            'type': content.meta_type,
            'url': absoluteURL(content, self.request),
            'path': self.get_content_path(content),
            'icon': IIconResolver(self.request).get_content_url(content),
            'title': content.get_title_or_id_editable(),
            'short_title': content.get_short_title_editable()
        })



class ICustomPathResources(IDefaultBrowserLayer):
    silvaconf.resource('custom_path.js')
    silvaconf.resource('custom_path.css')


class CustomPathWidget(FieldWidget):
    MODE = 'custom_path'
    grok.adapts(TextLineField, Interface, Interface)
    grok.name(MODE)

    def update(self):
        super(CustomPathWidget, self).update()
        need(ICustomPathResources)
        int_id = component.getUtility(IIntIds).register(self.form.context)
        self._htmlAttributes['data-lookup-url'] = self.lookup_url
        self._htmlAttributes['data-target-id'] = str(int_id)

    @Lazy
    def service(self):
        service = closest_custom_short_url_service(self.form.context)
        return service

    @Lazy
    def lookup_url(self):
        return absoluteURL(self.service, self.request) + \
            '/++rest++silva.app.shorturl.custom_path_lookup?custom_path='


class ShortURLForm(silvaforms.SMISubForm):

    label = _(u'Short URL')

    grok.view(Settings)
    grok.context(ISilvaObject)
    grok.order(100)
    fields = silvaforms.Fields(ShortURLFields)
    fields['custom_path'].mode = 'custom_path'

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
