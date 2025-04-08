from qgis.core import QgsApplication
from processing_provider.elevation_tile_provider import ElevationTileForJpProcessingProvider

class YourPluginName():

    def __init__(self):
        self.provider = None

    def initProcessing(self):
        self.provider = ElevationTileForJpProcessingProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)