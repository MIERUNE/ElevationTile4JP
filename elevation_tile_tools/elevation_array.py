import urllib

import numpy as np


class ElevationArray:
    def __init__(self, zoom_level, start_path, end_path):
        self.zoom_level = zoom_level
        self.start_path = start_path
        self.end_path = end_path

    # タイル座標から標高タイルを読み込む
    @staticmethod
    def fetch_tile(z, x, y):
        tile_URL = "https://cyberjapandata.gsi.go.jp/xyz/dem/{}/{}/{}.txt".format(z, x, y)
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
        print("取得タイル数:{}枚".format(number_of_tile))

        if number_of_tile > 100:
            raise Exception("取得するタイルが大きすぎます。処理を停止します")
        all_array = np.concatenate([np.concatenate([self.fetch_tile(
            self.zoom_level, x, y) for y in y_length], axis=0) for x in x_length], axis=1)

        if (all_array == -9999).all():
            raise Exception("指定の範囲に標高タイルは存在しません")
        return all_array
