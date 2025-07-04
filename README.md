# ElevationTile4JP
![](icon.png)

## Overview
This is a QGIS plugin that downloads Japan DEM elevation tiles and converts them to GeoTiff.
<br>
![](./img/mov.gif)


## Usage

- 1 Click plugin icon or select `ElevationTile4JP --> ElevationTile4JP DEM Downloader` in Processing Toolbox.

<img src="img/processing.png" alt="dialog screenshot" width="600"/>

- 2 Select tiles zoom level
- 3 Select the output file CRS
- 4 Set the area of interest. Extent can be set with:
  - Layer: target layer extent
  - Layout Map: target layout map extent
  - Bookmark: extent saved on bookmark
  - Map Canvas Extent: current map canvas extent
  - Draw on Canvas: draw customize extent on map canvas
- 5 Set the output file
- 6 Click OK and the processed file will be added to the map canvas

<img src="img/dialog.png" alt="dialog screenshot" width="600"/>

## Data source
[Elevation tile](https://maps.gsi.go.jp/development/ichiran.html#dem) of [Geospatial Information Authority of Japan](https://www.gsi.go.jp/)

## Note
- This plugin is ready-to-use, but the data source will be decimated during the process. If you need accurate data, use [QuickDEM4JP](https://github.com/MIERUNE/QuickDEM4JP).
- Downloadable amount is limited to 1000 tiles. A lower zoom level has to be considered if the limited tiles amount is reached.
- The original tile coordinate reference system is web mercator (EPSG:3857) and exported file will be reprojected to the input value.

---

### License
GNU GENERAL PUBLIC LICENSE 2