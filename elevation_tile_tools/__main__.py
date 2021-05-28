from pathlib import Path

import click as click

from elevation_tile_tools.elevation_tile_converter import \
    ElevationTileConverter


@click.command()
@click.option(
    "--output_path",
    "-o",
    required=False,
    type=str,
    default="./GeoTiff",
    help="GeoTiffを格納するディレクトリ default=./GeoTiff",
)
@click.option(
    "--epsg",
    "-e",
    required=False,
    type=str,
    default="EPSG:3857",
    help="出力するGeoTiffのEPSGコード default=EPSG:3857",
)
@click.option(
    "--zoom_level",
    "-z",
    required=False,
    type=int,
    default=10,
    help="取得するタイルのズームレベル default=10",
)
@click.option("--bbox",
              "-b",
              required=False,
              type=str,
              default=[141.24847412109375, 42.974511174899156, 141.48193359375, 43.11702412135048],
              help="取得したい標高タイルの範囲を指定 default="
                   "[141.24847412109375,42.974511174899156,141.48193359375,43.11702412135048]",
              )
def main(output_path, epsg, zoom_level, bbox):
    if isinstance(bbox, str):
        bbox = eval(bbox)
    if not is_bbox(bbox):
        raise Exception("bboxが不正です")

    elevation_tile = ElevationTileConverter(
        output_path=Path(output_path),
        output_epsg=epsg,
        zoom_level=zoom_level,
        bbox=bbox
    )
    elevation_tile.calc()


def is_bbox(bbox):
    if not isinstance(bbox, list):
        print("bboxは配列形式で指定してください")
        return False
    if len(bbox) != 4:
        print("bboxの配列には数値を4つだけ入れてください")
        return False
    return True


if __name__ == '__main__':
    main()
