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

_DESCRIPTION = """
Download Japan DEM tiles from the <a href='https://maps.gsi.go.jp/development/ichiran.html#dem'>Geospatial Information Authority of Japan (GSI)</a> and convert to GeoTiff<br>
<a href='https://maps.gsi.go.jp/development/ichiran.html#dem'>国土地理院の標高タイル</a>を取得しGeoTIFFに変換するプロセッシングツールです。
"""


class ElevationTile4JpProcessingAlgorithm(QgsProcessingAlgorithm):
    EXTENT = "EXTENT"
    ZOOM_LEVEL = "ZOOM_LEVEL"
    OUTPUT_PATH = "OUTPUT_PATH"
    OUTPUT_CRS_ID = "OUTPUT_CRS_ID"

    def tr(self, string):
        return QCoreApplication.translate("ElevationTile4JpProcessingAlgorithm", string)

    def createInstance(self):
        return ElevationTile4JpProcessingAlgorithm()

    def name(self):
        return "elevationtile4jp_algorithm"

    def displayName(self):
        return self.tr("Download Japan DEM Tiles")

    def shortHelpString(self):
        return self.tr(
            "Download Japan DEM tiles from the <a href='https://maps.gsi.go.jp/development/ichiran.html#dem'>Geospatial Information Authority of Japan (GSI)</a> and convert to GeoTiff"
        )

    def initAlgorithm(self, config=None):
        zoom_levels = [str(i) for i in range(15)]
        self.addParameter(
            QgsProcessingParameterEnum(
                self.ZOOM_LEVEL,
                self.tr("Elevation tile zoom level"),
                options=zoom_levels,
                defaultValue=9,
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_PATH, self.tr("Output DEM tiles"), optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterCrs(
                self.OUTPUT_CRS_ID,
                self.tr("Output file CRS"),
                defaultValue="EPSG:4326",
            )
        )
        self.addParameter(
            QgsProcessingParameterExtent(
                self.EXTENT,
                self.tr("Extent"),
                optional=False,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        feedback.pushInfo(self.tr("Starting ElevationTile4JP process..."))
        # ---------------- ズームレベル ---------------- #
        zoom_levels = [str(i) for i in range(15)]
        zoom_level_index = self.parameterAsEnum(parameters, self.ZOOM_LEVEL, context)
        zoom_level = int(zoom_levels[zoom_level_index])

        # ---------------- 出力パス ---------------- #
        output_path = self.parameterAsOutputLayer(parameters, self.OUTPUT_PATH, context)

        out_dir = out_dir = os.path.dirname(output_path) or os.getcwd()
        if not os.path.exists(out_dir):
            feedback.reportError(
                self.tr("Output folder does not exists: {}").format(out_dir)
            )
            return {}

        if not os.access(out_dir, os.W_OK):
            feedback.reportError(
                self.tr("Cannot write on specified output folder: {}").format(out_dir)
            )
            return {}

        # ---------------- 出力CRS ---------------- #
        output_crs_id = self.parameterAsCrs(
            parameters, self.OUTPUT_CRS_ID, context
        ).authid()

        # ---------------- BBox 取得 ---------------- #
        extent = self.parameterAsExtent(parameters, self.EXTENT, context)
        # CRS 変換
        try:
            extent_crs = self.parameterAsExtentCrs(parameters, self.EXTENT, context)
            source_crs = QgsProject.instance().crs()

            # Unify CRS extent to project CRS
            if extent_crs != source_crs:
                transform = QgsCoordinateTransform(
                    extent_crs, source_crs, QgsProject.instance()
                )
                extent = transform.transformBoundingBox(extent)

            dest_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            transform = QgsCoordinateTransform(
                source_crs, dest_crs, QgsProject.instance()
            )
            transformed_extent = transform.transformBoundingBox(extent)

            if transformed_extent.isEmpty():
                feedback.reportError(
                    self.tr("Specified extent is empty after reprojection.")
                )
                return {}
        except Exception as e:
            feedback.reportError(
                self.tr("Failed to reproject specified extent: {}").format(str(e))
            )
            return {}

        if transformed_extent.xMinimum() > transformed_extent.xMaximum():
            feedback.reportError(
                self.tr(
                    "Cannot specify an extent crossing the international date line."
                )
            )
            return {}

        bbox = [
            transformed_extent.xMinimum(),
            transformed_extent.yMinimum(),
            transformed_extent.xMaximum(),
            transformed_extent.yMaximum(),
        ]

        # ---------------- パラメータ設定 ---------------- #
        converter = ElevationTileConverter(
            output_path=output_path,
            zoom_level=zoom_level,
            bbox=bbox,
            output_crs_id=output_crs_id,
            feedback=feedback,
        )

        feedback.pushInfo(f"{converter.number_of_tiles} founded")

        if converter.number_of_tiles > converter.max_number_of_tiles:
            feedback.reportError(
                self.tr(
                    "Too many tiles. Please specify a lower zoom level or smaller extent to get less than  {} tiles."
                ).format(converter.max_number_of_tiles)
            )
            return {}
        elif converter.number_of_tiles > converter.large_number_of_tiles:
            feedback.pushWarning(
                self.tr("Downloading {} tiles may take a while.").format(
                    converter.number_of_tiles
                )
            )

        # ---------------- 実行 ---------------- #
        try:
            converter.run()
            converter.create_geotiff()
        except Exception as e:
            feedback.reportError(
                self.tr("An error occured during process: {}").format(str(e))
            )
            return {}

        feedback.pushInfo(self.tr("GeoTIFF created."))

        return {self.OUTPUT_PATH: output_path}
