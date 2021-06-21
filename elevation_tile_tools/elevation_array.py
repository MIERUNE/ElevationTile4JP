import urllib

import numpy as np



class TileQuantityException(Exception):
    def __init__(self, max_number_of_tiles, number_of_tiles):
        self.number_of_tiles = number_of_tiles
        self.max_number_of_tiles = max_number_of_tiles

    def __str__(self):
        return ("The number of tiles to get is too large. \n"
                f"Maximum number of tiles to get is {self.max_number_of_tiles}. Intended to get {self.number_of_tiles} tiles.")


class ElevationArray:
    def __init__(self, zoom_level, start_path, end_path):
        self.max_number_of_tiles = 100
        self.zoom_level = zoom_level
        self.start_path = start_path
        self.end_path = end_path

    # タイル座標から標高タイルを読み込む
    @staticmethod
    def fetch_tile(z, x, y):
        tile_URL = "https://cyberjapandata.gsi.go.jp/xyz/dem/{}/{}/{}.txt".format(
            z, x, y)
        try:
            csv_file = urllib.request.urlopen(tile_URL)
            array = np.genfromtxt(
                csv_file, delimiter=",", filling_values=-9999)
        except urllib.error.HTTPError:
            array = np.full((256, 256), -9999)
        return array

    # 範囲内の全ての標高タイルをマージ
    def fetch_all_tiles(self):
        x_length = range(self.start_path[0], self.end_path[0] + 1)
        y_length = range(self.start_path[1], self.end_path[1] + 1)

        number_of_tile = len(x_length) * len(y_length)
        print("number of tiles:{}".format(number_of_tile))

        if number_of_tile > self.max_number_of_tiles:
            raise TileQuantityException(number_of_tile)
        all_array = np.concatenate([np.concatenate([self.fetch_tile(
            self.zoom_level, x, y) for y in y_length], axis=0) for x in x_length], axis=1)

        if (all_array == -9999).all():
            raise Exception(
                "The specified extent is out of range from the provided dem tiles")
        return all_array
