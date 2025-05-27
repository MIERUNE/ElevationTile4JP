from pathlib import Path

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .elevation_tile_algorithm import ElevationTile4JpProcessingAlgorithm


class ElevationTileForJpProcessingProvider(QgsProcessingProvider):
    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(ElevationTile4JpProcessingAlgorithm())

    def id(self, *args, **kwargs):
        return "elevationtile4jp"

    def name(self, *args, **kwargs):
        return self.tr("ElevationTile4JP")

    def icon(self):
        path = (Path(__file__).parent / "icon.png").resolve()
        return QIcon(str(path))
