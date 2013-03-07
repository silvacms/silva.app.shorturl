# -*- coding: utf-8 -*-
# Copyright (c) 2002-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from setuptools import setup, find_packages
import os

version = '3.0'

tests_require = [
    'Products.Silva [test]',
    'silva.app.forest [test]',
    ]

setup(name='silva.app.shorturl',
      version=version,
      description="Short url generation for silva",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Framework :: Zope2",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='silva shorturl',
      author='Infrae',
      author_email='info@infrae.com',
      url='http://infrae.com/products/silva',
      license='BSD',
      package_dir={'': 'src'},
      packages=find_packages('src'),
      namespace_packages=['silva', 'silva.app'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'Products.Silva',
        'five.grok',
        'setuptools',
        'silva.app.forest',
        'silva.core.conf',
        'silva.core.interfaces',
        'silva.core.services',
        'silva.core.smi',
        'silva.core.views',
        'silva.fanstatic',
        'silva.translations',
        'silva.ui',
        'zope.component',
        'zope.interface',
        'zope.schema',
        'zope.publisher',
        'zope.intid',
        ],
      tests_require=tests_require,
      extras_require={'test': tests_require},
      )
