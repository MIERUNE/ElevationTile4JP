from qgis.core import QgsApplication
from qgis._gui import QgisInterface
from .processing_provider.elevation_tile_provider import ElevationTileForJpProcessingProvider

class ElevationTile4JpPlugin:

    def __init__(self, iface: QgisInterface):
        self.iface = iface

    def initProcessing(self):
        self.provider = ElevationTileForJpProcessingProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
