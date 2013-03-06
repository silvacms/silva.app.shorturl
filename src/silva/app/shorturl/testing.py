# -*- coding: utf-8 -*-
# Copyright (c) 2013  Infrae. All rights reserved.
# See also LICENSE.txt

from silva.app.forest.testing import SilvaAppForestLayer

import transaction
import silva.app.shorturl


class ShortURLLayer(SilvaAppForestLayer):
    default_packages = SilvaAppForestLayer.default_packages + [
        'silva.app.shorturl',
        ]

    def _install_application(self, app):
        super(ShortURLLayer, self)._install_application(app)
        app.root.service_extensions.install('silva.app.shorturl')
        transaction.commit()


FunctionalLayer = ShortURLLayer(silva.app.shorturl)
