from math import log, pi, tan

import pyproj


class TileCoordinate:
    def __init__(
            self,
            zoom_level=10,
            bbox=None,
    ):
        # x_min, y_min, x_max, y_max
        if bbox is None:
            bbox = [
                141.24847412109375,
                42.974511174899156,
                141.48193359375,
                43.11702412135048,
            ]
        self.zoom_level: int = zoom_level
        self.bbox: [float] = bbox

    # 四隅の緯度経度（Webメルカトル）を配列で受け取ってタイル座標のminmaxを取得
    # QGISなどでWebメルカトルの背景地図を表示させた時に、画面範囲に背景地図のない部分が入っているとエラー
    def tile_coordinates_of_corner(self, corner_xy_list, zoom):
        corner_latlon_list = [self.xy_to_latlon(xy) for xy in corner_xy_list]
        tile_coordinates = [self.latlon_to_tile_coordinate(
            latlon[0], latlon[1], zoom) for latlon in corner_latlon_list]

        assert tile_coordinates[1][0] < tile_coordinates[2][0], "取得開始タイル番号より終了タイル番号の方が大きくなっています。"

        tile_numbers = {
            "start_x": tile_coordinates[1][0],
            "end_x": tile_coordinates[2][0],
            "start_y": tile_coordinates[1][1],
            "end_y": tile_coordinates[2][1],
        }
        return tile_numbers

    # WebメルカトルのXY座標を緯度経度に変換
    @staticmethod
    def xy_to_latlon(xy_coordinate: list):
        x = xy_coordinate[0]
        y = xy_coordinate[1]
        src_crs = pyproj.Proj(init="EPSG:4326")
        dest_crs = pyproj.Proj(init="EPSG:4326")
        lon, lat = pyproj.transform(src_crs, dest_crs, x, y)
        return [lat, lon]

    # 緯度経度からタイル座標を算出
    @staticmethod
    def latlon_to_tile_coordinate(lat, lon, zoom_level):
        x = int((lon / 180 + 1) * 2 ** zoom_level / 2)
        y = int(((-log(tan((45 + lat / 2) * pi / 180)) + pi)
                 * 2 ** zoom_level / (2 * pi)))
        return [x, y]

    # 四隅のXY座標の組み合わせをリストで取得
    @staticmethod
    def make_corner_xy_from_bbox(bbox):
        xmin, ymin, xmax, ymax = bbox
        lower_left_XY = [xmin, ymin]
        upper_left_XY = [xmin, ymax]
        lower_right_XY = [xmax, ymin]
        upper_right_XY = [xmax, ymax]
        return [lower_left_XY, upper_left_XY, lower_right_XY, upper_right_XY]

    # タイル座標を全て取得してリストに格納、左上と右下のタイル座標を返す
    def make_all_tile_coords(self, tile_numbers, zoom_level):
        start_x_tile = tile_numbers["start_x"]
        end_x_tile = tile_numbers["end_x"]
        start_y_tile = tile_numbers["start_y"]
        end_y_tile = tile_numbers["end_y"]

        # xyタイルの枚数
        number_of_x_tile = (end_x_tile - start_x_tile) + 1
        number_of_y_tile = (end_y_tile - start_y_tile) + 1
        # 処理中のタイル番号
        x_tile_number = start_x_tile
        y_tile_number = start_y_tile

        tile_coordinates = []
        for i in range(0, number_of_x_tile):
            for j in range(0, number_of_y_tile):
                tile_coordinates.append([x_tile_number, y_tile_number])
                y_tile_number += 1
            x_tile_number += 1
            y_tile_number = start_y_tile

        return tile_coordinates

    @staticmethod
    def create_tile_paths(tile_numbers, tile_coordinates):
        start_x_tile = tile_numbers["start_x"]
        end_x_tile = tile_numbers["end_x"]
        start_y_tile = tile_numbers["start_y"]
        end_y_tile = tile_numbers["end_y"]

        start_path = tile_coordinates[0]
        end_path = tile_coordinates[-1]

        # Geotiff変換用に取得範囲の左下と右上のタイル座標を取得
        x_min = min(range(start_x_tile, end_x_tile + 1))
        y_max = max(range(start_y_tile, end_y_tile + 1))
        lower_left_tile_path = [x_min, y_max]

        x_max = max(range(start_x_tile, end_x_tile + 1))
        y_min = min(range(start_y_tile, end_y_tile + 1))
        upper_light_tile_path = [x_max, y_min]
        return start_path, end_path, lower_left_tile_path, upper_light_tile_path

    # bboxの範囲内のタイル座標を割り出して四隅を返却する
    def calc_tile_coordinates(self):
        tile_numbers = self.tile_coordinates_of_corner(
            self.make_corner_xy_from_bbox(self.bbox), self.zoom_level
        )

        tile_coordinates = self.make_all_tile_coords(
            tile_numbers,
            self.zoom_level,
        )

        start_path, end_path, lower_left_tile_path, upper_light_tile_path = self.create_tile_paths(
            tile_numbers, tile_coordinates)

        return start_path, end_path, lower_left_tile_path, upper_light_tile_path
