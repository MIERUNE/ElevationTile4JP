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
    help="Directory to output file. default=./GeoTiff",
)
@click.option(
    "--projection",
    "-p",
    required=False,
    type=str,
    default="EPSG:3857",
    help="CRS of output tiff. Specify with EPSG code. default=EPSG:3857",
)
@click.option(
    "--zoom_level",
    "-z",
    required=False,
    type=int,
    default=10,
    help="Tile zoomlevel to get. default=10",
)
@click.option(
    "--bbox",
    "-b",
    required=False,
    type=str,
    default=[141.24847412109375, 42.974511174899156, 141.48193359375, 43.11702412135048],
    help="Extent of DEM tile to get. Specify with bounding box. default="
        "[141.24847412109375,42.974511174899156,141.48193359375,43.11702412135048]",
    )
def main(output_path, crs_id, zoom_level, bbox):
    if isinstance(bbox, str):
        bbox = eval(bbox)
    if not is_bbox(bbox):
        raise Exception("The bbox is invalid.")

    elevation_tile = ElevationTileConverter(
        output_path=Path(output_path),
        output_crs_id=crs_id,
        zoom_level=zoom_level,
        bbox=bbox
    )
    elevation_tile.calc()


def is_bbox(bbox):
    if not isinstance(bbox, list):
        print("Specify the bbox with list.")
        return False
    if len(bbox) != 4:
        print("The number of values are invalid. Specify 4 values.")
        return False
    return True


if __name__ == '__main__':
    main()
