from math import atan, exp, pi
from pathlib import Path

import pyproj

from elevation_tile_tools.elevation_array import ElevationArray
from elevation_tile_tools.geotiff import GeoTiff
from elevation_tile_tools.tile_coordinate import TileCoordinate


class ElevationTileConverter:
    def __init__(
        self,
        output_path=Path(__file__).parent.parent / "GeoTiff",
        output_epsg="EPSG:3857",
        zoom_level=10,
        bbox=None
    ):
        # x_min, y_min, x_max, y_max
        if bbox is None:
            bbox = [
                141.24847412109375,
                42.974511174899156,
                141.48193359375,
                43.11702412135048,
            ]
        self.output_path = output_path
        if not self.output_path.exists():
            self.output_path.mkdir(parents=True, exist_ok=True)
        self.zoom_level = zoom_level
        self.bbox = bbox
        self.output_epsg = output_epsg
        self.tile_coordinate = TileCoordinate(self.zoom_level, self.bbox)
        self.params_for_creating_geotiff = []

    # 緯度経度をWebメルカトルのXY座標に変換
    @staticmethod
    def transform_latlon_to_xy(latlon):
        src_crs = pyproj.Proj(init="EPSG:4326")
        dest_crs = pyproj.Proj(init="EPSG:3857")
        lat = latlon[0]
        lon = latlon[1]
        # 地図の端部は若干85と180をはみ出て原点の位置が座標系の変換時にずれるのでそれを修正
        if lat < -85:
            lat = -85.05112877980659
        elif lat > 85:
            lat = 85.05112877980659

        if lon < -180:
            lon = int(-180)
        elif lon > 180:
            lon = int(180)
        print("lat", lat)
        print("lon", lon)
        X, Y = pyproj.transform(src_crs, dest_crs, lon, lat)

        print("X, Y", X, Y)
        return [X, Y]

    # タイル座標から、そのタイルの左下・右上の緯度経度を算出
    @staticmethod
    def tile_to_pixel_coordinate_of_corner(
            z, x_tile_coordinate, y_tile_coordinate):
        # 楕円体の長半径
        ellipsoid_radius = 6378137
        # タイル原点(0,0)のXY座標
        org_x = -1 * (2 * ellipsoid_radius * pi / 2)
        org_y = 2 * ellipsoid_radius * pi / 2
        # 楕円体の円周をタイルの枚数で割ってタイル1枚の距離を算出
        unit = 2 * ellipsoid_radius * pi / (2 ** z)
        # タイルの原点からタイル座標までの距離を算出
        x = org_x + x_tile_coordinate * unit
        y = org_y - y_tile_coordinate * unit

        # 左下・右上の緯度経度を算出
        lower_left_lat = atan(
            exp((y - unit) * pi / 20037508.34)) * 360 / pi - 90
        lower_left_lon = x * 180 / 20037508.34
        lower_left_latlon = [lower_left_lat, lower_left_lon]

        upper_right_lat = atan(exp(y * pi / 20037508.34)) * 360 / pi - 90
        upper_right_lon = (x + unit) * 180 / 20037508.34
        upper_right_latlon = [upper_right_lat, upper_right_lon]

        return lower_left_latlon, upper_right_latlon

    # 一括処理を行うメソッド
    def calc(self):
        start_path, end_path, lower_left_tile_path, upper_light_tile_path = self.tile_coordinate.calc_tile_coordinates()

        self.elevation_array = ElevationArray(
            self.zoom_level, start_path, end_path)
        np_array = self.elevation_array.fetch_all_tiles()
        x_length = np_array.shape[1]
        y_length = np_array.shape[0]

        lower_left_latlon = self.tile_to_pixel_coordinate_of_corner(
            self.zoom_level, lower_left_tile_path[0], lower_left_tile_path[1]
        )[0]
        upper_right_latlon = self.tile_to_pixel_coordinate_of_corner(
            self.zoom_level, upper_light_tile_path[0], upper_light_tile_path[1]
        )[1]
        print(
            "lower_left_latlon",
            lower_left_latlon,
            "upper_right_latlon",
            upper_right_latlon,
        )

        lower_left_XY = self.transform_latlon_to_xy(lower_left_latlon)
        upper_right_XY = self.transform_latlon_to_xy(upper_right_latlon)
        print("lower_left_XY", lower_left_XY, "upper_right_XY", upper_right_XY)

        # 座標の右側の絶対値から左側の絶対値を引く
        # どっちもプラス、マイナスなら、絶対値の大きい方から小さい方を引く
        pixel_size_x = None
        pixel_size_y = None
        if upper_right_XY[0] >= 0 and lower_left_XY[0] >= 0:
            pixel_size_x = (
                abs(upper_right_XY[0]) - abs(lower_left_XY[0])) / x_length
            pixel_size_y = - \
                (abs(upper_right_XY[1]) - abs(lower_left_XY[1])) / y_length
        elif upper_right_XY[0] <= 0 and lower_left_XY[0] <= 0:
            pixel_size_x = (
                abs(upper_right_XY[0]) - abs(lower_left_XY[0])) / x_length
            pixel_size_y = - \
                (abs(upper_right_XY[1]) - abs(lower_left_XY[1])) / y_length
        # 片方がプラスなら絶対値を足す
        elif upper_right_XY[0] <= 0 <= lower_left_XY[0]:
            pixel_size_x = (
                abs(upper_right_XY[0]) + abs(lower_left_XY[0])) / x_length
            pixel_size_y = - \
                (abs(upper_right_XY[1]) + abs(lower_left_XY[1])) / y_length
        elif upper_right_XY[0] >= 0 >= lower_left_XY[0]:
            pixel_size_x = (
                abs(upper_right_XY[0]) + abs(lower_left_XY[0])) / x_length
            pixel_size_y = - \
                (abs(upper_right_XY[1]) + abs(lower_left_XY[1])) / y_length

        print("pixel_size_x", pixel_size_x, "pixel_size_y", pixel_size_y)

        print("左上:", lower_left_XY[0], upper_right_XY[1])
        print("右下:", upper_right_XY[0], lower_left_XY[1])

        self.params_for_creating_geotiff = [
            np_array,
            lower_left_XY[0],
            upper_right_XY[1],
            pixel_size_x,
            pixel_size_y,
            x_length,
            y_length,
        ]

        geotiff = GeoTiff(self.output_path)
        geotiff.write_geotiff(
            np_array,
            lower_left_XY[0],
            upper_right_XY[1],
            pixel_size_x,
            pixel_size_y,
            x_length,
            y_length,
        )

        if not self.output_epsg == "EPSG:3857":
            geotiff.resampling("EPSG:3857", self.output_epsg)