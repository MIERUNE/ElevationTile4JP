from qgis.core import QgsApplication
from qgis.gui import QgisInterface

from elevation_tile_for_jp import ElevationTileForJP
from get_tiles import GetTilesWithinMapCanvas

def test_show_dialog(plugin: ElevationTileForJP):
    plugin.dialog_show()
    assert isinstance(plugin.get_tiles_within_mapcanvas, GetTilesWithinMapCanvas)
