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


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ElevationTile4JP class from file ElevationTile4JP.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .elevation_tile_for_jp import ElevationTileForJP
    return ElevationTileForJP(iface)
