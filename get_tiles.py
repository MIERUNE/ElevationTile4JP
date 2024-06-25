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
from math import log

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QThread
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
)
from qgis.gui import QgsFileWidget

from elevation_tile_for_jp_dialog import ElevationTileforJPDialog

from elevation_tile_tools import ElevationTileConverter

from progress_dialog import ProgressDialog


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
            QgsFileWidget.StorageMode.SaveFile
        )

        # プロジェクトのデフォルトのcrsを格納
        self.dlg.mQgsProjectionSelectionWidget_output_crs.setCrs(self.project.crs())

        # set extent as current map canvas with current CRS
        # QgsExtentGroupBox
        self.dlg.mExtentGroupBox.setMapCanvas(iface.mapCanvas())
        self.dlg.mExtentGroupBox.setOutputCrs(QgsProject.instance().crs())
        self.dlg.mExtentGroupBox.setOutputExtentFromCurrent()
        QgsProject.instance().crsChanged.connect(self.on_map_crs_changed)

        # コンボボックスにズームレベルを設定
        self.setup_zoom_level_combo_box()

        # ダイアログのボタンボックスがaccepted（OK）されたらcalcが作動
        self.dlg.button_box.accepted.connect(self.calc)
        # ダイアログのボタンボックスがrejected（キャンセル）されたらdlg_cancel()が作動
        self.dlg.button_box.rejected.connect(self.dlg_cancel)

        self.process_interrupted = False

    # update extent crs when updated
    def on_map_crs_changed(self):
        (self.dlg.mExtentGroupBox.setOutputCrs(QgsProject.instance().crs()),)
        self.dlg.mExtentGroupBox.setOutputExtentFromCurrent()

    # キャンセルクリック
    def dlg_cancel(self):
        # ダイアログを非表示
        self.dlg.hide()

    def set_interrupted(self):
        self.process_interrupted = True

    def on_abort_clicked(
        self, thread: QThread, progress_dialog: ProgressDialog
    ) -> None:
        if QMessageBox.Yes == QMessageBox.question(
            None,
            progress_dialog.translate("Aborting"),
            progress_dialog.translate("Are you sure to cancel process?"),
            QMessageBox.Yes,
            QMessageBox.No,
        ):
            self.set_interrupted()
            self.abort_process(thread, progress_dialog)

    def handle_process_failed(
        self, error_message, thread: QThread, progress_dialog: ProgressDialog
    ) -> None:
        progress_dialog.close()
        QMessageBox.information(None, progress_dialog.translate("Error"), error_message)
        self.set_interrupted()
        self.abort_process(thread, progress_dialog)

    def abort_process(self, thread: QThread, progress_dialog: ProgressDialog) -> None:
        if self.process_interrupted:
            thread.exit()
            progress_dialog.abort_dialog()
            self.dlg_cancel()
            return

    # 一括処理を行うメソッド
    def calc(self):
        geotiff_output_path = self.dlg.mQgsFileWidget_output.filePath()
        output_crs = self.dlg.mQgsProjectionSelectionWidget_output_crs.crs()
        project_crs = self.project.crs()
        zoom_level = int(self.dlg.comboBox_zoomlevel.currentText())
        bbox = self.transform(project_crs, self.get_canvas_bbox())

        # elevation tiles converter process thread
        thread = ElevationTileConverter(
            output_path=geotiff_output_path,
            output_crs_id=output_crs.authid(),
            zoom_level=zoom_level,
            bbox=bbox,
        )

        # initialize process dialog
        progress_dialog = ProgressDialog(thread.set_abort_flag)

        # 入力値のバリデーション
        if geotiff_output_path == "":
            QMessageBox.information(
                None,
                progress_dialog.translate("Error"),
                progress_dialog.translate("Output file is not defined."),
            )
            return

        # check if directory exists
        directory = os.path.dirname(geotiff_output_path)
        if not os.path.isdir(directory):
            QMessageBox.information(
                None,
                progress_dialog.translate("Error"),
                "{}\n{}".format(
                    progress_dialog.translate("Cannot find output folder."), directory
                ),
            )
            return

        # Add .tiff to output path if missing
        if not geotiff_output_path.lower().endswith(".tiff"):
            geotiff_output_path += ".tiff"

        output_crs_isvalid = output_crs.isValid()
        if not output_crs_isvalid:
            QMessageBox.information(
                None,
                progress_dialog.translate("Error"),
                progress_dialog.translate("CRS of output file is not defined."),
            )
            return

        # 標準時子午線を跨ぐ領域指定はタイルを取得できないので処理を中断する
        xmin, _, xmax, _ = bbox
        if xmin > xmax:
            QMessageBox.information(
                None,
                progress_dialog.translate("Error"),
                progress_dialog.translate(
                    "Target extent must not cross the International Date Line meridian."
                ),
            )
            return

        # check number of tiles
        if thread.number_of_tiles > thread.max_number_of_tiles:
            error_message = (
                progress_dialog.translate("Too large amount of tiles ({})") + " \n"
            )

            error_message += progress_dialog.translate(
                "Set a lower zoom level or extent to get less than {} tiles."
            )

            error_message = error_message.format(
                thread.number_of_tiles, thread.max_number_of_tiles
            )

            QMessageBox.information(
                None, progress_dialog.translate("Error"), error_message
            )
            return

        elif thread.number_of_tiles > thread.large_number_of_tiles:
            message = progress_dialog.translate(
                "Dowloading {} tiles may take a while. Process anyway?"
            ).format(thread.number_of_tiles)

            if QMessageBox.No == QMessageBox.question(
                None,
                progress_dialog.translate("Warning"),
                message,
                QMessageBox.Yes,
                QMessageBox.No,
            ):
                return

        progress_dialog.set_abortable(False)
        progress_dialog.abortButton.clicked.connect(
            lambda: [
                self.on_abort_clicked(thread, progress_dialog),
            ]
        )

        # progress dialog orchestation by process thread
        thread.setMaximum.connect(progress_dialog.set_maximum)
        thread.addProgress.connect(progress_dialog.add_progress)
        thread.postMessage.connect(progress_dialog.set_message)
        thread.setAbortable.connect(progress_dialog.set_abortable)
        thread.processFinished.connect(progress_dialog.close)
        thread.processFailed.connect(
            lambda error_message: [
                self.handle_process_failed(error_message, thread, progress_dialog)
            ]
        )

        # タイル取得処理の実行
        thread.start()
        progress_dialog.exec_()

        # do not import if processed has been interrupted
        if self.process_interrupted:
            return

        # Tiffを作成
        thread.create_geotiff()

        # 出力ファイルをマップキャンバスに追加する
        self.project.addMapLayer(
            QgsRasterLayer(
                geotiff_output_path,
                os.path.splitext(os.path.basename(geotiff_output_path))[0],
            )
        )

        self.iface.messageBar().pushInfo(
            "ElevationTile4JP",
            progress_dialog.translate("DEM exported to Geotiff Format."),
        )

        self.dlg_cancel()

    def get_current_zoom(self):
        scale = self.iface.mapCanvas().scale()
        dpi = self.iface.mainWindow().physicalDpiX()
        maxScalePerPixel = 156543.04
        inchesPerMeter = 39.37
        return int(
            round(log(((dpi * inchesPerMeter * maxScalePerPixel) / scale), 2), 0)
        )

    # 対象領域のXY座標のminとmaxを取得
    def get_canvas_bbox(self):
        extent = [
            self.dlg.mExtentGroupBox.outputExtent().xMinimum(),
            self.dlg.mExtentGroupBox.outputExtent().yMinimum(),
            self.dlg.mExtentGroupBox.outputExtent().xMaximum(),
            self.dlg.mExtentGroupBox.outputExtent().yMaximum(),
        ]
        return extent

    def transform(self, src_crs, bbox, dst_crs_id="EPSG:4326"):
        dst_crs = QgsCoordinateReferenceSystem(dst_crs_id)
        coord_transform = QgsCoordinateTransform(src_crs, dst_crs, self.project)

        lower_left = coord_transform.transform(bbox[0], bbox[1])
        upper_right = coord_transform.transform(bbox[2], bbox[3])

        return [lower_left.x(), lower_left.y(), upper_right.x(), upper_right.y()]

    # コンボボックスにズームレベルを設定するメソッド
    def setup_zoom_level_combo_box(self):
        max_zoom_level = 14
        current_zoom_level = self.get_current_zoom()

        for i in range(0, max_zoom_level + 1):
            self.dlg.comboBox_zoomlevel.addItem(str(i))

        if current_zoom_level > max_zoom_level:
            current_zoom_level = max_zoom_level

        self.dlg.comboBox_zoomlevel.setCurrentText(str(current_zoom_level))
