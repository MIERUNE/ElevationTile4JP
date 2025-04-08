from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterCrs,
    QgsProcessingParameterExtent
)
from ..elevation_tile_tools.elevation_tile_converter import ElevationTileConverter


class ElevationTile4JpProcessingAlgorithm(QgsProcessingAlgorithm):

    BBOX = 'BBOX'
    ZOOM_LEVEL = 'ZOOM_LEVEL'
    OUTPUT_CRS = 'OUTPUT_CRS'
    OUTPUT_FOLDER = 'OUTPUT_FOLDER'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ElevationTile4JpProcessingAlgorithm()

    def name(self):
        return 'elevationtile4jp_algorithm'

    def displayName(self):
        return self.tr('ElevationTile4JP DEM Downloader')

    def group(self):
        return self.tr('Elevation Tools')

    def groupId(self):
        return 'elevation_tools'

    def shortHelpString(self):
        return self.tr('国土地理院の標高タイルを取得しGeoTIFFに変換するプロセッシングツールです。')

    def initAlgorithm(self, config=None):
        # ズームレベル
        zoom_levels = [str(i) for i in range(15)]  # 0から14までのズームレベルを生成
        self.addParameter(
            QgsProcessingParameterEnum(
            self.ZOOM_LEVEL,
            self.tr('Elevation tile zoom level'),
            options=zoom_levels,
            defaultValue=9,
            optional=True
            )
        )
        # 出力ファイルパス
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_FILE,
                self.tr('Output file path'),
                fileFilter='GeoTIFF files (*.tif)',
                optional=True,
                defaultValue='output.tif'
            )
        )
        # 出力ファイルCRS（座標参照系）
        self.addParameter(
            QgsProcessingParameterCrs(
                self.OUTPUT_CRS,
                self.tr('Output file CRS'),
                defaultValue='EPSG:4326',
                optional=True
            )
        )
        # 取得範囲（Extent）
        self.addParameter(
            QgsProcessingParameterExtent(
                self.EXTENT,
                self.tr('Extent'),
                defaultValue='141.24,42.97,141.48,43.11',
                optional=True
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        bbox = [float(c) for c in parameters[self.BBOX].split(',')]
        zoom_level = int(parameters[self.ZOOM_LEVEL])
        output_crs = parameters[self.OUTPUT_CRS]
        output_folder = parameters[self.OUTPUT_FOLDER]

        feedback.pushInfo("ElevationTile4JP処理開始...")

        converter = ElevationTileConverter(
            output_path=output_folder,
            zoom_level=zoom_level,
            bbox=bbox,
            output_crs_id=output_crs
        )

        converter.run(feedback)
        converter.create_geotiff()

        feedback.pushInfo("GeoTIFF作成完了しました。")

        return {}