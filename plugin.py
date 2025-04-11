import contextlib

from PyQt5.QtWidgets import QAction, QToolButton
from qgis.core import QgsApplication
from qgis.gui import QgisInterface

from .processing_provider.elevation_tile_provider import (
    ElevationTileForJpProcessingProvider,
)
from .processing_provider.elevation_tile_algorithm import (
    ElevationTile4JpProcessingAlgorithm,
)

with contextlib.suppress(ImportError):
    from processing import execAlgorithmDialog


class ElevationTile4JpPlugin:

    def __init__(self, iface: QgisInterface):
        self.iface = iface
        self.provider = None
        self.toolButtonAction = None

    def initProcessing(self):
        if not self.provider:
            self.provider = ElevationTileForJpProcessingProvider()
            QgsApplication.processingRegistry().addProvider(self.provider)

    def unloadProcessing(self):
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None

    def initGui(self):
        self.initProcessing()
        self._setup_algorithm_tool_button()

    def unload(self):
        self._teardown_algorithm_tool_button()
        self.unloadProcessing()

    def _setup_algorithm_tool_button(self):
        if self.toolButtonAction:
            return

        icon = self.provider.icon()

        tool_button = QToolButton()
        default_action = QAction(
            icon,
            self.tr("ElevationTile4JP: DEM Downloader"),
            self.iface.mainWindow(),
        )

        provider_id = self.provider.id()
        algorithm_id = ElevationTile4JpProcessingAlgorithm().name()
        algo_id = f"{provider_id}:{algorithm_id}"

        default_action.triggered.connect(
            lambda: execAlgorithmDialog(algo_id, {})
        )

        tool_button.setDefaultAction(default_action)

        self.toolButtonAction = self.iface.addToolBarWidget(tool_button)

    def _teardown_algorithm_tool_button(self):
        if self.toolButtonAction:
            self.iface.removeToolBarIcon(self.toolButtonAction)
            self.toolButtonAction = None

    def tr(self, message: str) -> str:
        return QgsApplication.translate("ElevationTile4JP", message)