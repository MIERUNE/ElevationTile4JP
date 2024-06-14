import urllib

import numpy as np

from PyQt5.QtWidgets import QMessageBox


class ElevationArray:
    max_number_of_tiles = 1000
    large_number_of_tiles = 100

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

        # if number_of_tiles > self.max_number_of_tiles:
        #     raise TileQuantityException(self.max_number_of_tiles, number_of_tiles)
        # elif number_of_tiles > self.large_number_of_tiles:
        #     message = (
        #         f"取得タイル数({number_of_tiles}枚)が多いため、処理に時間がかかる可能性があります。"
        #         "ダウンロードを実行しますか？"
        #     )
        #     if QMessageBox.No == QMessageBox.question(
        #         None,
        #         "確認",
        #         message,
        #         QMessageBox.Yes,
        #         QMessageBox.No,
        #     ):
        #         raise UserTerminationException

        return number_of_tiles
