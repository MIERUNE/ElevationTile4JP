# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ElevationTile4JP
                                 A QGIS plugin
 画面内の標高タイルを取得し、GeoTiffに変換します

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

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'elevation_tile_for_jp_dialog_base.ui'))


class ElevationTileforJPDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(ElevationTileforJPDialog, self).__init__(parent)
        self.setupUi(self)
