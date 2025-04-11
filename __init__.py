# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ElevationTile4JP
                                 A QGIS plugin
 The plugin to convert GSI elevation tile to GeoTiff.
                             -------------------
        begin                : 2021-05-31
        git sha              : $Format:%H$
        copyright            : (C) 2021 by MIERUNE Inc.
        email                : info@mierune.co.jp
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
import sys

from qgis._gui import QgisInterface

from .plugin import ElevationTile4JpPlugin

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "elevation_tile_tools"))


def classFactory(iface: QgisInterface):
    """
    Entrypoint for QGIS plugin.
    """

    return ElevationTile4JpPlugin(iface)