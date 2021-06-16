import os
from math import log

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import *

from .elevation_tile_for_jp_dialog import ElevationTileforJPDialog

from .elevation_tile_tools import ElevationTileConverter

import warnings

warnings.simplefilter("ignore", ResourceWarning)


class GetTilesWithinMapCanvas:

    # ダイアログの初期表示等の処理はここに記載する
    def __init__(self, iface):
        self.iface = iface
        self.project = QgsProject.instance()
        self.dlg = ElevationTileforJPDialog()
        self.project_dir = self.project.homePath()

        # ダイアログのobject_nameに対してメソッドを指定。デフォルトのパスをセット
        self.dlg.mQgsFileWidget_output.setFilePath(self.project_dir)

        # 出力ファイルの指定が出来るようにする
        self.dlg.mQgsFileWidget_output.setFilter("*.tiff")
        self.dlg.mQgsFileWidget_output.setStorageMode(
            QgsFileWidget.StorageMode.SaveFile)
        self.dlg.mQgsFileWidget_output.setDialogTitle(
            "保存ファイルを選択してください")
        # プロジェクトのデフォルトのcrsを格納
        self.dlg.mQgsProjectionSelectionWidget_output_crs.setCrs(
            self.project.crs())

        for i in range(0, 15):
            self.dlg.comboBox_zoomlevel.addItem(str(i))

        self.dlg.comboBox_zoomlevel.setCurrentText(
            str(self.get_current_zoom()))

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
        geotiff_output_path = self.dlg.mQgsFileWidget_output.filePath()
        output_crs = self.dlg.mQgsProjectionSelectionWidget_output_crs.crs()
        project_crs = self.project.crs()
        zoom_level = int(self.dlg.comboBox_zoomlevel.currentText())
        bbox = self.transfrom(project_crs, self.get_canvas_bbox())

        # 入力値のバリデーション
        if geotiff_output_path == "":
            self.iface.messageBar().pushWarning(
                u"ELEVATIONTILE4JP", u"出力ファイル名を指定してください。")
            return

        output_crs_isvalid = output_crs.isValid()
        if not output_crs_isvalid:
            self.iface.messageBar().pushWarning(
                u"ELEVATIONTILE4JP", u"出力ファイルの座標系が指定されていません。座標系を指定してください。")
            return

        # 標準時子午線を跨ぐ領域指定はタイルを取得できないので処理を中断する
        xmin, _, xmax, _ = bbox
        if xmin > xmax:
            self.iface.messageBar().pushWarning(
                u"ELEVATIONTILE4JP", u"タイル取得範囲が不正です。マップキャンバスの表示範囲は西経180度から東経180度の範囲を表示してください。")
            return
        print(output_crs.authid())
        elevation_tile = ElevationTileConverter(
            output_path=geotiff_output_path,
            output_crs_id=str(output_crs.authid()),
            zoom_level=zoom_level,
            bbox=bbox
        )
        elevation_tile.calc()

        self.project.addMapLayer(QgsRasterLayer(geotiff_output_path, os.path.splitext(
            os.path.basename(geotiff_output_path))[0]))

        self.dlg_cancel()

        self.iface.messageBar().pushInfo(
                u"ELEVATIONTILE4JP", u"GeoTiff形式のDEMを出力しました。")

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

    def transfrom(self, src_crs, bbox, dest_crs=4326):
        coord_transform = QgsCoordinateTransform(
            src_crs, QgsCoordinateReferenceSystem(dest_crs), self.project)

        lower_left = coord_transform.transform(bbox[0], bbox[1])
        upper_right = coord_transform.transform(bbox[2], bbox[3])

        return [lower_left.x(), lower_left.y(), upper_right.x(), upper_right.y()]
