# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from zope.interface import Interface

from silva.core import conf as silvaconf
from silva.core.conf.installer import DefaultInstaller

SERVICE_NAME = 'service_shorturls'
SHORT_URL_PREFIX = '$'

silvaconf.extension_name("silva.app.shorturl")
silvaconf.extension_title("Silva Short URL")
silvaconf.extension_depends(['Silva'])


class SilvaShortURLInstaller(DefaultInstaller):
    """ Silva shorturl installer
    """

    service_name = SERVICE_NAME

    def install_custom(self, root):
        installed_ids = root.objectIds()
        if SERVICE_NAME not in installed_ids:
            factory = root.manage_addProduct['silva.app.shorturl']
            factory.manage_addShortURLService(SERVICE_NAME)
        resolver_name = SERVICE_NAME + '_resolver'
        if resolver_name not in installed_ids:
            factory = root.manage_addProduct['silva.app.shorturl']
            factory.manage_addShortURLResolverService(resolver_name)


class IExtension(Interface):
    """silva.app.shorturl extension
    """


install = SilvaShortURLInstaller("silva.app.shorturl", IExtension)

