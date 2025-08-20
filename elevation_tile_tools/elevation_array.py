import urllib

import numpy as np


class ElevationArray:
    def __init__(self, zoom_level, start_path, end_path):
        self.zoom_level = zoom_level
        self.start_path = start_path
        self.end_path = end_path
        self.x_length = range(self.start_path[0], self.end_path[0] + 1)
        self.y_length = range(self.start_path[1], self.end_path[1] + 1)

    # タイル座標から標高タイルを読み込む
    @staticmethod
    def fetch_tile(z, x, y):
        tile_URL = f"https://cyberjapandata.gsi.go.jp/xyz/dem/{z}/{x}/{y}.txt"
        try:
            csv_file = urllib.request.urlopen(tile_URL)
            array = np.genfromtxt(csv_file, delimiter=",", filling_values=-9999)
        except urllib.error.HTTPError:
            array = np.full((256, 256), -9999)
        return array

    # 範囲内の全ての標高タイルをマージ

    def count_tiles(self) -> int:
        number_of_tiles = len(self.x_length) * len(self.y_length)
        print(f"number of tiles:{number_of_tiles}")

        return number_of_tiles
