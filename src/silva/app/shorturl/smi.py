# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope import component
from zope import schema
from zope.cachedescriptors.property import Lazy
from zope.interface import Interface
from zope.intid.interfaces import IIntIds
from zope.location.interfaces import ISite
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.traversing.browser import absoluteURL

from silva.core import conf as silvaconf
from silva.core.interfaces import ISilvaObject, ContentError, ISilvaNameChooser
from silva.core.interfaces.adapters import IIconResolver
from silva.core.smi.settings import SettingsMenu, Settings
from silva.core.views import views as silvaviews
from silva.fanstatic import need
from silva.translations import translate as _
from silva.ui.menu import MenuItem
from silva.ui.rest import UIREST

from zeam.form import silva as silvaforms
from zeam.form.base.interfaces import IWidget
from zeam.form.base.widgets import FieldWidget
#from zeam.form.ztk.interfaces import ICollectionField
from zeam.form.ztk.widgets.collection import newCollectionWidgetFactory
from zeam.form.ztk.widgets.collection import MultiGenericDisplayFieldWidget
from zeam.form.ztk.widgets.collection import SetField
from zeam.form.ztk.widgets.textline import TextLineField

from .interfaces import IShortURLService
from .service import closest_short_url_service, closest_site
from . import SHORT_URL_PREFIX


class ShortURLTool(silvaforms.SMIComposedForm):
    """ Short URL Tool.
    """
    grok.adapts(Settings, ISilvaObject)
    grok.name('shorturl')
    grok.require('silva.ChangeSilvaContent')

    label = _(u'Short URL Tool')
    description = _(u'This screen lets you manage and customize Short URLs. The URLs link directly to the public view of this item.')

    def available(self):
        return bool(component.queryUtility(IShortURLService)) and not \
            ISite.providedBy(self.context)


class ShortURLMenu(MenuItem):
    grok.adapts(SettingsMenu, ISilvaObject)
    grok.order(10000)
    grok.require('silva.ChangeSilvaContent')
    name = _(u'Short URL Tool')
    screen = ShortURLTool


class ShortURLInformation(silvaviews.Viewlet):
    grok.context(ISilvaObject)
    grok.order(100)
    grok.view(Settings)
    grok.viewletmanager(silvaforms.SMIFormPortlets)

    @Lazy
    def service(self):
        return component.queryUtility(IShortURLService)

    @Lazy
    def short_url_service(self):
        return closest_short_url_service(self.context)

    def available(self):
        return self.short_url is not None or \
            self.custom_short_url is not None

    def update(self):
        self.short_url = None
        self.custom_short_url = None

        if self.service is not None:
            self.short_url = self.service.get_short_url(
                self.context, self.request)

        if self.short_url_service is not None:
            pass
            # XXX: FIXME
            # self.custom_short_url = \
            #     self.short_url_service.get_custom_short_url(
            #         self.context,
            #         self.request)


class ShortURLFields(Interface):
    short_url = schema.TextLine(
        title=_(u"Short URL for this item"),
        description=_(u"Highlight and copy the Short URL for use in other communications."),
        required=False)
    custom_paths = schema.Set(
        title=_(u'Custom Short URLs'),
        description = _(u"Highlight and copy a URL."),
        required=False,
        value_type=schema.TextLine(title=_(u"Custom Short URLs"),
                                   required=False))



class CustomShortURLFields(Interface):
    custom_path = schema.TextLine(
        title=_(u"Custom Short URL"),
        description=_(u"Create a memorable Custom Short URL for use in other media."),
        required=True)



def validate_custom_path(value, form):
    if value is silvaforms.NO_VALUE:
        return _(u'A required value is missing.')
    try:
        service = closest_short_url_service(form.context)
        site = closest_site(service)
        ISilvaNameChooser(site).checkName(value, None)
    except ContentError as e:
        return e.reason
    return None


class RESTCustomShortPathInfo(UIREST):
    grok.context(IShortURLService)
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


class IDisplayShortURLResources(IDefaultBrowserLayer):
    silvaconf.resource('display_shorturl.js')


class ShortURLWidget(FieldWidget):
    grok.baseclass()

    @Lazy
    def service(self):
        service = closest_short_url_service(self.form.context)
        return service

    @Lazy
    def base_url(self):
        if self.service is not None:
            url = self.service.get_prefix_url(self.request)
            if url is not None:
                return url.rstrip('/') + '/'
        return None


class DisplayShortURLWidget(ShortURLWidget):
    MODE = 'display_shorturl'
    grok.adapts(TextLineField, Interface, Interface)
    grok.name(MODE)

    def update(self):
        super(DisplayShortURLWidget, self).update()
        need(IDisplayShortURLResources)

    def inputValue(self):
        value = super(DisplayShortURLWidget, self).inputValue()
        if value:
            return self.base_url.rstrip('/') + '/' + value
        return value

grok.global_adapter(
    newCollectionWidgetFactory(mode='display_shorturl'),
    adapts=(SetField, Interface, Interface),
    provides=IWidget,
    name='display_shorturl')


class SetFieldWidget(MultiGenericDisplayFieldWidget):
    grok.adapts(SetField, Interface, Interface, Interface)
    grok.name('display_shorturl')


class CustomPathWidget(ShortURLWidget):
    MODE = 'custom_path'
    grok.adapts(TextLineField, Interface, Interface)
    grok.name(MODE)

    def update(self):
        super(CustomPathWidget, self).update()
        need(ICustomPathResources)
        int_id = component.getUtility(IIntIds).register(self.form.context)
        self._htmlAttributes['data-lookup-url'] = self.lookup_url
        self._htmlAttributes['data-target-id'] = str(int_id)
        self._htmlAttributes['size'] = '24'
        self._htmlAttributes['placeholder'] = _(u'Shortcut...')

    @Lazy
    def lookup_url(self):
        return absoluteURL(self.service, self.request) + \
            '/++rest++silva.app.shorturl.custom_path_lookup?custom_path='


class ShortURLFormBase(silvaforms.SMISubForm):
    grok.baseclass()
    grok.view(ShortURLTool)
    grok.context(ISilvaObject)

    ignoreContent = True
    ignoreRequest = True

    @Lazy
    def site(self):
        if self.short_url_service is not None:
            return closest_site(self.short_url_service)

    def get_custom_short_path(self):
        return self.short_url_service.get_custom_short_path(self.context)

    @Lazy
    def short_url_service(self):
        return closest_short_url_service(self.context)


def custom_short_paths_default(form):
    return form.short_url_service.get_custom_short_paths(form.context)

def short_url_default(form):
    return SHORT_URL_PREFIX + form.short_url_service.get_short_path(
        form.context)

def custom_paths_available(form):
    return bool(form.short_url_service.get_custom_short_paths(form.context))


class ShortURLForm(ShortURLFormBase):

    label = _(u'Short URLs')
    description = _(u'<DESCRIPTION SHORT URL DISPLAY FORM does not display>')

    grok.order(100)
    fields = silvaforms.Fields(ShortURLFields)
    mode = 'display_shorturl'

    fields['custom_paths'].available = custom_paths_available
    fields['custom_paths'].defaultValue = custom_short_paths_default
    fields['short_url'].defaultValue = short_url_default

    # @silvaforms.action(title=_(u"Clear custom path"), **{
    #     'data-confirmation': _(u'Are you sure you want to clear'
    #                             ' the custom short path ?')})
    # def clear_custom_path(self):
    #     self.short_url_service.unregister_custom_short_path(
    #         self.context)
    #     return silvaforms.SUCCESS


class SaveCustomPathAction(silvaforms.Action):

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        form.short_url_service.register_custom_short_path(
            data.get('custom_path'), form.context)
        return silvaforms.SUCCESS


class CustomShortURLForm(ShortURLFormBase):

    label = _(u'Add a Custom Short URL')
    description = _(u'<DESCRIPTION ADD CUSTOM SHORT URL FORM does not display>')

    grok.view(ShortURLTool)
    grok.context(ISilvaObject)
    grok.order(101)
    fields = silvaforms.Fields(CustomShortURLFields)
    fields['custom_path'].mode = 'custom_path'
    fields['custom_path'].validate = validate_custom_path

    actions = silvaforms.Actions(SaveCustomPathAction(_(u"Add a Custom Short URL")))
