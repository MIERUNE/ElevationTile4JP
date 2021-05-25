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
        self.project = QgsProject.instance()

        # ダイアログのobject_nameに対してメソッドを指定。デフォルトのパスをセット
        self.dlg.mQgsFileWidget.setFilePath(self.project.homePath())

        # ディレクトリの指定が出来るようにする
        self.dlg.mQgsFileWidget.setStorageMode(QgsFileWidget.GetDirectory)

        for i in range(0, 15):
            self.dlg.comboBox.addItem(str(i))

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
        output_crs = self.dlg.mQgsProjectionSelectionWidget.crs().authid()
        zoom_level = self.canvas_zoomlevel()
        xmin, xmax, ymin, ymax = self.canvas_XY_coordinate_of_minmax()
        bbox = [xmin, ymin, xmax, ymax]

        elevation_tile = ElevationTileConverter(
            output_path=geotiff_output_path,
            output_epsg=output_crs,
            zoom_level=zoom_level,
            bbox=bbox
        )
        elevation_tile.calc()

        QgsRasterLayer(str(geotiff_output_path.joinpath('merge.tiff')), 'merge')
        QgsRasterLayer(str(geotiff_output_path.joinpath('warp.tiff')), 'warp')
