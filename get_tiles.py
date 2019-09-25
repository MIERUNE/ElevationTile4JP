import osr
from osgeo import gdal
import pyproj
from math import log, tan, pi, e, atan, exp
import sys
import numpy as np
import os
import requests
import urllib.request, urllib.error
# import pandas as pd

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import *

from .elevation_tiles_to_geotiff_dialog import ElevationTilesToGeoTiffDialog


class GetTilesWithinMapCanvas:

    # ダイアログの初期表示等の処理はここに記載する
    def __init__(self, iface):
        self.iface = iface
        self.dlg = ElevationTilesToGeoTiffDialog()

        self.current_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'GeoTiff')

        # ダイアログのobject_nameに対してメソッドを指定。デフォルトのパスをセット
        self.dlg.mQgsFileWidget.setFilePath(self.current_dir)
        
        # ディレクトリの指定が出来るようにする
        self.dlg.mQgsFileWidget.setStorageMode(QgsFileWidget.GetDirectory)

        for i in range(2, 15):
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
        self.geotiff_output_path = self.dlg.mQgsFileWidget.filePath()
        output_crs = self.dlg.mQgsProjectionSelectionWidget.crs().authid()

        xmin, xmax, ymin, ymax = self.canvas_XY_coordinate_of_minmax()
        corner_XY_coordinate_list = self.corner_XY_coordinate_list(xmin, xmax, ymin, ymax)
        zoomlevel = self.canvas_zoomlevel()
        start_X_tile, end_X_tile, start_Y_tile, end_Y_tile, zoomlevel = self.tile_coordinates_of_corner(corner_XY_coordinate_list, zoomlevel)
        start_path, end_path, lower_left_tile_path, upper_light_tile_path = self.all_tiles_store_in_list(start_X_tile, end_X_tile, start_Y_tile, end_Y_tile, zoomlevel)
        # 左上（start）から右下（end）のタイル座標から標高タイルを取得してマージ
        array = self.fetch_all_tiles(start_path, end_path)
        xlen = array.shape[1]
        ylen = array.shape[0]

        print('xlen', xlen, 'ylen', ylen)

        lower_left_latlon = self.tile_to_pixel_coordinate_of_corner(zoomlevel, lower_left_tile_path[1], lower_left_tile_path[2])[0]
        upper_right_latlon = self.tile_to_pixel_coordinate_of_corner(zoomlevel, upper_light_tile_path[1], upper_light_tile_path[2])[1]

        lower_left_XY = self.transform_latlon_to_XY(lower_left_latlon)
        upper_right_XY = self.transform_latlon_to_XY(upper_right_latlon)

        pixel_size_x = (upper_right_XY[0] - lower_left_XY[0]) / xlen
        pixel_size_y = (lower_left_XY[1] - upper_right_XY[1]) / ylen

        print('pixel_size_x', pixel_size_x, 'pixel_size_y', pixel_size_y)

        print('左上:', upper_right_XY[0], lower_left_XY[1])
        print('右下:', lower_left_XY[0], upper_right_XY[1])

        geotiff = self.write_geotiff(array, lower_left_XY[0], upper_right_XY[1], pixel_size_x, pixel_size_y, xlen, ylen)

        self.resampling('EPSG:3857', output_crs)
        print('warp:', output_crs)

        merge_layer = QgsRasterLayer(os.path.join(self.geotiff_output_path, 'merge.tif'), 'merge')
        warp_layer = QgsRasterLayer(os.path.join(self.geotiff_output_path, 'warp.tif'), 'warp')

        QgsProject.instance().addMapLayer(merge_layer)
        QgsProject.instance().addMapLayer(warp_layer)

    # mapcanvasのXY座標のminとmaxを取得
    def canvas_XY_coordinate_of_minmax(self):
        extent = self.iface.mapCanvas().extent()
        xmin, xmax, ymin, ymax =  float(extent.xMinimum()), float(extent.xMaximum()), float(extent.yMinimum()), float(extent.yMaximum())
        return [xmin, xmax, ymin, ymax]

    # 四隅のXY座標を取得
    def corner_XY_coordinate_list(self, xmin, xmax, ymin, ymax):
        lower_left_XY = [xmin, ymin]
        upper_left_XY = [xmin, ymax]
        lower_right_XY = [xmax, ymin]
        upper_right_XY = [xmax, ymax]
        return [lower_left_XY, upper_left_XY, lower_right_XY, upper_right_XY]

    # mapcanvasのズームレベルを算出
    def canvas_zoomlevel(self):
        scale = self.iface.mapCanvas().scale()
        dpi = self.iface.mainWindow().physicalDpiX()
        maxScalePerPixel = 156543.04
        inchesPerMeter = 39.37
        current_zoomlevel = int(round(log(((dpi * inchesPerMeter * maxScalePerPixel) / scale), 2), 0))
        # if current_zoomlevel > 15:
        #     print('zoomlevelは14以下でないと標高タイルをダウンロード出来ません!zoomlevel14で標高タイルをダウンロードします')
        #     current_zoomlevel = 14
        zoomlevel = int(self.dlg.comboBox.currentText())
        print('zoomlevel:', zoomlevel)
        print('現在のzoomlevel:', current_zoomlevel)
        return zoomlevel

    # WebメルカトルのXY座標を緯度経度に変換
    def transform_XY_to_latlon(self, XY_coordinate):
        X = XY_coordinate[0]
        Y = XY_coordinate[1]
        src_crs = pyproj.Proj(init='EPSG:3857')
        dest_crs = pyproj.Proj(init='EPSG:4326')
        lon, lat = pyproj.transform(src_crs, dest_crs, X, Y)
        return [lat, lon]

    # 緯度経度をWebメルカトルのXY座標に変換
    def transform_latlon_to_XY(self, latlon):
        src_crs = pyproj.Proj(init='EPSG:4326')
        dest_crs = pyproj.Proj(init='EPSG:3857')
        lat = latlon[0]
        lon = latlon[1]
        X, Y = pyproj.transform(src_crs, dest_crs, lon, lat)
        return [X, Y]

    # 緯度経度からタイル座標を算出
    def latlon_to_tile_coordinate(self, lat, lon, zoomlevel):
        x = int((lon / 180 + 1) * 2 ** zoomlevel / 2)
        y = int(((-log(tan((45 + lat / 2) * pi / 180)) + pi) * 2 ** zoomlevel / (2 * pi)))
        print(x, y)
        return [x, y]

    # タイル座標から、そのタイルの左下・右上の緯度経度を算出
    def tile_to_pixel_coordinate_of_corner(self, z, xtile_coordinate, ytile_coordinate):
        # 楕円体の長半径
        ellipsoid_radius = 6378137
        # タイル原点(0,0)のXY座標
        org_x = -1 * (2 * ellipsoid_radius * pi / 2)
        org_y = (2 * ellipsoid_radius * pi / 2)
        # 楕円体の円周をタイルの枚数で割ってタイル1枚の距離を算出
        unit = 2 * ellipsoid_radius * pi / (2 ** z)
        # タイルの原点からタイル座標までの距離を算出
        x = org_x + xtile_coordinate * unit
        y = org_y - ytile_coordinate * unit

        # 左下・右上の緯度経度を算出
        lower_left_lat = atan(exp((y - unit) * pi / 20037508.34)) * 360 / pi - 90
        lower_left_lon = x * 180 / 20037508.34
        lower_left_latlon = [lower_left_lat, lower_left_lon]

        upper_right_lat = atan(exp(y * pi / 20037508.34)) * 360 / pi - 90
        upper_right_lon = (x + unit) * 180 / 20037508.34
        upper_right_latlon = [upper_right_lat, upper_right_lon]

        return lower_left_latlon, upper_right_latlon

    # 四隅の緯度経度（Webメルカトル）を配列で受け取ってタイル座標のminmaxを取得
    def tile_coordinates_of_corner(self, corner_XY_coordinate_list, zoomlevel):
        corner_latlon_coordinate_list = [self.transform_XY_to_latlon(XY_coordinate) for XY_coordinate in corner_XY_coordinate_list]
        tiles_coordinate_of_corner = []
        for c in corner_latlon_coordinate_list:
            tile_coordinate = self.latlon_to_tile_coordinate(c[0],
                                                             c[1],
                                                             zoomlevel)
            tiles_coordinate_of_corner.append(tile_coordinate)
        start_X_tile = tiles_coordinate_of_corner[1][0] # upper_left xmin
        end_X_tile = tiles_coordinate_of_corner[2][0] #lower_right xmax
        start_Y_tile = tiles_coordinate_of_corner[1][1] # upper_left ymin
        end_Y_tile = tiles_coordinate_of_corner[2][1] #lower_right ymax
        return start_X_tile, end_X_tile, start_Y_tile, end_Y_tile, zoomlevel

    # タイル座標を全て取得してリストに格納、左上と右下のタイル座標を返す
    def all_tiles_store_in_list(self, start_X_tile, end_X_tile, start_Y_tile, end_Y_tile, zoomlevel):
        X_tile = start_X_tile
        Y_tile = start_Y_tile
        count_X = (end_X_tile - start_X_tile) + 1
        count_Y = (end_Y_tile - start_Y_tile) + 1
        tile_coordinate_all = []
        for i in range(0, count_X):
            for j in range(0, count_Y):
                tile_coordinate_all.append([zoomlevel, X_tile, Y_tile])
                Y_tile += 1
            X_tile += 1
            Y_tile = start_Y_tile
        start_path = tile_coordinate_all[0]
        end_path = tile_coordinate_all[-1]

        # Geotiff変換用に取得範囲の左下と右上のタイル座標を取得
        xmin = min(range(start_X_tile, end_X_tile + 1))
        ymax = max(range(start_Y_tile, end_Y_tile + 1))
        lower_left_tile_path = [zoomlevel, xmin, ymax]

        xmax = max(range(start_X_tile, end_X_tile + 1))
        ymin = min(range(start_Y_tile, end_Y_tile + 1))
        upper_light_tile_path = [zoomlevel, xmax, ymin]

        return (start_path, end_path, lower_left_tile_path, upper_light_tile_path)

    # タイル座標から標高タイルを読み込む
    def fetch_tile(self, z, x, y):
        tile_URL = 'https://cyberjapandata.gsi.go.jp/xyz/dem/{}/{}/{}.txt'.format(z, x, y)
        # df = pd.read_csv(tile_URL, header=None).replace("e", 0)
        try:
            csv_file = urllib.request.urlopen(tile_URL)
            array = np.genfromtxt(csv_file, delimiter=',', filling_values=-9999)
            print('ダウンロードURL:', tile_URL)
            print(array.shape)
            print(array)
            # np.where(array == "e", -9999, array)
        except urllib.error.HTTPError:
            print('ダウンロードURL:', tile_URL)
            print("タイルが存在しません")
            # array = np.full((256, 256), -9999, dtype="int")
            array = np.full((256, 256), -9999)
            print(array.shape)
            print(array)
        return array

    # 範囲内の全ての標高タイルをマージ
    def fetch_all_tiles(self, start_path, end_path):
        z = start_path[0]
        x_range = range(start_path[1], end_path[1]+1)
        y_range = range(start_path[2], end_path[2]+1)
        get_tile_number = len(x_range) * len(y_range)
        print(x_range)
        print(y_range)
        print('取得タイル数:{}枚'.format(get_tile_number))
        if get_tile_number > 50:
            raise Exception('取得するタイルが大きすぎます。処理を停止します')
        return  np.concatenate([np.concatenate([self.fetch_tile(z, x, y) for y in y_range], axis=0) for x in x_range], axis=1)

    # アレイと座標、ピクセルサイズ、グリッドサイズからGeoTiffを作成
    def write_geotiff(self, array, lower_left_lon, upper_right_lat, pixel_size_x, pixel_size_y, xlen, ylen):
        # 「左下経度・東西解像度・回転（０で南北方向）・右上緯度・回転（０で南北方向）・南北解像度（北南方向であれば負）」
        geotransform = [lower_left_lon,
                        pixel_size_x,
                        0,
                        upper_right_lat,
                        0,
                        pixel_size_y]

        merge_tiff_file = 'merge.tif'
        tiffFile = os.path.join(self.geotiff_output_path, merge_tiff_file)

        # ドライバーの作成
        driver = gdal.GetDriverByName("GTiff")
        # ドライバーに対して「保存するファイルのパス・グリットセル数・バンド数・ラスターの種類・ドライバー固有のオプション」を指定してファイルを作成
        dst_ds = driver.Create(tiffFile, xlen, ylen, 1, gdal.GDT_Float32)
        # geotransformをセット
        dst_ds.SetGeoTransform(geotransform)

        # 作成したラスターの第一バンドを取得
        rband = dst_ds.GetRasterBand(1)
        # 第一バンドにアレイをセット
        rband.WriteArray(array)
        # nodataの設定
        rband.SetNoDataValue(-9999)

        # EPSGコードを引数にとる前処理？
        ref = osr.SpatialReference()
        # EPSGコードを引数にとる
        ref.ImportFromEPSG(3857)
        # ラスターに投影法の情報を入れる
        dst_ds.SetProjection(ref.ExportToWkt())

        # ディスクへの書き出し
        dst_ds.FlushCache()

    # 再投影
    def resampling(self, srcSRS, outputSRS):
        warp_path = os.path.join(self.geotiff_output_path, 'warp.tif')
        src_path = os.path.join(self.geotiff_output_path, 'merge.tif')
        resampledRas = gdal.Warp(warp_path, src_path, srcSRS=srcSRS, dstSRS=outputSRS, resampleAlg="near")

        resampledRas.FlushCache()
        resampledRas = None