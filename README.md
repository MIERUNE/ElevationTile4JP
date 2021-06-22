# ElevationTile4JP
![](icon.png)

## Overview
This is a QGIS plugin that downloads elevation tiles and converts them to GeoTiff.
<br>
![](./img/mov.gif)


## Usage
- Specify the area to get DEM with the map canvas
- Click plugin icon or select Plugin --> ElevationTile4JP in menu bar
- Select the zoom level of the tiles
- Set the name of the output file
- Select the outpu file CRS
- Click OK and the processed file will be added to the map canvas

![](img/dialog.png)

## Data source
[Elevation tile](https://maps.gsi.go.jp/development/ichiran.html#dem) of [Geospatial Information Authority of Japan](https://www.gsi.go.jp/)

## Note
- This plugin is ready-to-use but the data source will be decimated during the process. If you need accurate data, use [QuickDEM4JP](https://github.com/MIERUNE/QuickDEM4JP).
- The original tile coordinate reference system is web mercator (EPSG:3857) and exported file will be reprojected to the input value.

---

### License
GNU GENERAL PUBLIC LICENSE 2