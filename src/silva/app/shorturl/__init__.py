# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

from zope.interface import Interface

from silva.core import conf as silvaconf
from silva.core.conf.installer import DefaultInstaller

from .interfaces import ISitemapService

silvaconf.extension_name("silva.app.shorturl")
silvaconf.extension_title("Silva shorturl")
silvaconf.extension_depends(['Silva'])


class SilvaShortURLInstaller(DefaultInstaller):
    """ Silva shorturl installer
    """

    service_name = 'service_shorturl'

    def install_custom(self, root):
        if self.service_name not in root.objectIds():
            factory = root.manage_addProduct['silva.app.shorturl']
            factory.manage_addShortURLService(self.service_name)


class IExtension(Interface):
    """silva.app.shorturl extension
    """


install = SilvaShortURLInstaller("silva.app.shorturl", IExtension)
