
from Products.Silva.testing import SilvaLayer

import transaction
import silva.app.shorturl


class ShortURLLayer(SilvaLayer):
    default_packages = SilvaLayer.default_packages + [
        'silva.app.shorturl',
        ]

    def _install_application(self, app):
        super(ShortURLLayer, self)._install_application(app)
        app.root.service_extensions.install('silva.app.shorturl')
        transaction.commit()


FunctionalLayer = ShortURLLayer(silva.app.shorturl)
