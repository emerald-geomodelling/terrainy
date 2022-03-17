#!/usr/bin/env python

import setuptools
import os

setuptools.setup(
    name='terrainy',
    version='0.0.1',
    description='Auto-downloader for global terrain data',
    long_description="""Library to generate rasterised images of 
    global height data such as DTM's. """,
    long_description_content_type="text/markdown",
    author='Ed Harrison',
    author_email='eh@emrld.no',
    url='https://github.com/emerald-geomodelling/terrainy',
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_data={'terrainy': ['*/*.geojson']},
    install_requires=[
        "rasterio",
        "geopandas",
        "shapely",
        "fiona",
        "owslib",
        "numpy",
        "rtree",
        "click"
    ],
    entry_points={
        'terrainy.connection': [
            'wcs = terrainy.connection_wcs:WcsConnection',
            'wms = terrainy.connection_wms:WmsConnection',
            'tile = terrainy.connection_tile:TileConnection',
        ],
        'console_scripts': [
            'terrainy = terrainy.cmd:main',
        ],
    },
)
