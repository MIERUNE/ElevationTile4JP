from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProcessingAlgorithm,
    QgsProcessingParameterCrs,
    QgsProcessingParameterEnum,
    QgsProcessingParameterExtent,
    QgsProcessingParameterRasterDestination,
    QgsProject,
)
from qgis.PyQt.QtCore import QCoreApplication

from ..elevation_tile_tools.elevation_tile_converter import ElevationTileConverter


class ElevationTile4JpProcessingAlgorithm(QgsProcessingAlgorithm):

    EXTENT = 'EXTENT'
    ZOOM_LEVEL = 'ZOOM_LEVEL'
    OUTPUT_PATH = 'OUTPUT_PATH'
    OUTPUT_CRS_ID = 'OUTPUT_CRS_ID'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ElevationTile4JpProcessingAlgorithm()

    def name(self):
        return 'elevationtile4jp_algorithm'

    def displayName(self):
        return self.tr('ElevationTile4JP DEM Downloader')

    def shortHelpString(self):
        return self.tr('国土地理院の標高タイルを取得しGeoTIFFに変換するプロセッシングツールです。')

    def initAlgorithm(self, config=None):
        zoom_levels = [str(i) for i in range(15)]
        self.addParameter(
            QgsProcessingParameterEnum(
                self.ZOOM_LEVEL,
                self.tr('Elevation tile zoom level'),
                options=zoom_levels,
                defaultValue=9,
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_PATH,
                self.tr("Output file"),
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterCrs(
                self.OUTPUT_CRS_ID,
                self.tr('Output file CRS'),
                defaultValue='EPSG:4326',
            )
        )
        self.addParameter(
            QgsProcessingParameterExtent(
                self.EXTENT,
                self.tr('Extent'),
                optional=False,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        feedback.pushInfo("ElevationTile4JP処理開始...")

        zoom_levels = [str(i) for i in range(15)]
        zoom_level_index = self.parameterAsEnum(parameters, self.ZOOM_LEVEL, context)
        zoom_level = int(zoom_levels[zoom_level_index])

        output_path = self.parameterAsOutputLayer(parameters, self.OUTPUT_PATH, context)

        output_crs_id = self.parameterAsCrs(parameters, self.OUTPUT_CRS_ID, context).authid()

        extent = self.parameterAsExtent(parameters, self.EXTENT, context)

        source_crs = QgsProject.instance().crs()
        dest_crs = QgsCoordinateReferenceSystem('EPSG:4326')

        try:
            transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
            transformed_extent = transform.transformBoundingBox(extent)
        except Exception as e:
            feedback.reportError(f"座標変換に失敗しました: {str(e)}")
            return {}

        bbox = [
            transformed_extent.xMinimum(),
            transformed_extent.yMinimum(),
            transformed_extent.xMaximum(),
            transformed_extent.yMaximum()
        ]

        try:
            converter = ElevationTileConverter(
                output_path=output_path,
                zoom_level=zoom_level,
                bbox=bbox,
                output_crs_id=output_crs_id
            )
            converter.run()
            converter.create_geotiff()
        except Exception as e:
            feedback.reportError(f"標高タイル作成中にエラーが発生しました: {str(e)}")
            return {}

        feedback.pushInfo("GeoTIFF作成完了しました。")

        return {self.OUTPUT_PATH: output_path}