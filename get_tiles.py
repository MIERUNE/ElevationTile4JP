import os
from math import log
from pathlib import Path

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import *

from .elevation_tiles_to_geotiff_dialog import ElevationTilesToGeoTiffDialog

from .elevation_tile_tools import ElevationTileConverter


class GetTilesWithinMapCanvas:

    # ダイアログの初期表示等の処理はここに記載する
    def __init__(self, iface):
        self.iface = iface
        self.dlg = ElevationTilesToGeoTiffDialog()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))

        # ダイアログのobject_nameに対してメソッドを指定。デフォルトのパスをセット
        self.dlg.mQgsFileWidget.setFilePath(self.current_dir)

        # ディレクトリの指定が出来るようにする
        self.dlg.mQgsFileWidget.setStorageMode(QgsFileWidget.GetDirectory)

        # プロジェクトのデフォルトのcrsを格納
        self.dlg.mQgsProjectionSelectionWidget.setCrs(QgsProject.instance().crs())

        for i in range(0, 15):
            self.dlg.comboBox.addItem(str(i))

        self.dlg.comboBox.setCurrentText(str(self.get_current_zoom()))

        # ダイアログのボタンボックスがaccepted（OK）されたらcalcが作動
        self.dlg.button_box.accepted.connect(self.calc)
        # ダイアログのボタンボックスがrejected（キャンセル）されたらdlg_cancel()が作動
        self.dlg.button_box.rejected.connect(self.dlg_cancel)

    # キャンセルクリック
    def dlg_cancel(self):
        # ダイアログを非表示
        self.dlg.hide()

    # 一括処理を行うメソッド
    def calc(self):
        geotiff_output_path = Path(self.dlg.mQgsFileWidget.filePath())
        output_crs = self.dlg.mQgsProjectionSelectionWidget.crs()
        project_crs = QgsProject.instance().crs()
        zoom_level = int(self.dlg.comboBox.currentText())
        bbox = self.trunsfrom(project_crs, self.get_canvas_bbox())

        elevation_tile = ElevationTileConverter(
            output_path=geotiff_output_path,
            output_epsg=f"EPSG:{output_crs.postgisSrid()}",
            zoom_level=zoom_level,
            bbox=bbox
        )
        elevation_tile.calc()

        QgsRasterLayer(str(geotiff_output_path.joinpath('merge.tiff')), 'merge')
        QgsRasterLayer(str(geotiff_output_path.joinpath('warp.tiff')), 'warp')

    def get_current_zoom(self):
        scale = self.iface.mapCanvas().scale()
        dpi = self.iface.mainWindow().physicalDpiX()
        maxScalePerPixel = 156543.04
        inchesPerMeter = 39.37
        return int(round(log(((dpi * inchesPerMeter * maxScalePerPixel) / scale), 2), 0))

    # map_canvasのXY座標のminとmaxを取得
    def get_canvas_bbox(self):
        extent = self.iface.mapCanvas().extent()
        xmin, xmax, ymin, ymax = float(
            extent.xMinimum()), float(
            extent.xMaximum()), float(
            extent.yMinimum()), float(
                extent.yMaximum())
        return [xmin, ymin, xmax, ymax]

    def trunsfrom(self, src_crs, bbox, dest_crs=4326):
        coord_transform = QgsCoordinateTransform(
            src_crs, QgsCoordinateReferenceSystem(dest_crs), QgsProject.instance())

        lower_left = coord_transform.transform(bbox[0], bbox[1])
        upper_right = coord_transform.transform(bbox[2], bbox[3])

        return [lower_left.x(), lower_left.y(), upper_right.x(), upper_right.y()]
