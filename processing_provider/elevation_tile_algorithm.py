import os

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
        # ---------------- ズームレベル ---------------- #
        zoom_levels = [str(i) for i in range(15)]
        zoom_level_index = self.parameterAsEnum(parameters, self.ZOOM_LEVEL, context)
        zoom_level = int(zoom_levels[zoom_level_index])

        # ---------------- 出力パス ---------------- #
        output_path = self.parameterAsOutputLayer(parameters, self.OUTPUT_PATH, context)

        out_dir = out_dir = os.path.dirname(output_path) or os.getcwd()
        if not os.path.exists(out_dir):
            feedback.reportError(f"出力先のディレクトリが存在しません: {out_dir}")
            return {}

        if not os.access(out_dir, os.W_OK):
            feedback.reportError(f"出力先のディレクトリに書き込み権限がありません: {out_dir}")
            return {}

        # ---------------- 出力CRS ---------------- #
        output_crs_id = self.parameterAsCrs(parameters, self.OUTPUT_CRS_ID, context).authid()

        # ---------------- BBox 取得 ---------------- #
        extent = self.parameterAsExtent(parameters, self.EXTENT, context)
        # CRS 変換
        try:
            source_crs = QgsProject.instance().crs()
            dest_crs = QgsCoordinateReferenceSystem('EPSG:4326')
            transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
            transformed_extent = transform.transformBoundingBox(extent)

            if transformed_extent.isEmpty():
                feedback.reportError("変換された範囲が空です。")
                return {}
        except Exception as e:
            feedback.reportError(f"座標変換に失敗しました: {str(e)}")
            return {}

        if transformed_extent.xMinimum() > transformed_extent.xMaximum():
            feedback.reportError("国際日付変更線を越える範囲は指定できません。")
            return {}

        bbox = [
            transformed_extent.xMinimum(),
            transformed_extent.yMinimum(),
            transformed_extent.xMaximum(),
            transformed_extent.yMaximum()
        ]

        # ---------------- パラメータ設定 ---------------- #
        converter = ElevationTileConverter(
            output_path=output_path,
            zoom_level=zoom_level,
            bbox=bbox,
            output_crs_id=output_crs_id
        )

        if converter.number_of_tiles > converter.max_number_of_tiles:
            feedback.reportError(
                f"タイルの数が多すぎます。最大{converter.max_number_of_tiles}個までです。"
            )
            return {}
        elif converter.number_of_tiles > converter.large_number_of_tiles:
            feedback.pushWarning(
                f"{converter.number_of_tiles} タイルをダウンロードします。時間がかかる可能性があります。"
            )

        # ---------------- 実行 ---------------- #
        try:
            converter.run()
            converter.create_geotiff()
        except Exception as e:
            feedback.reportError(f"標高タイル作成中にエラーが発生しました: {str(e)}")
            return {}

        feedback.pushInfo("GeoTIFF作成完了しました。")

        return {self.OUTPUT_PATH: output_path}