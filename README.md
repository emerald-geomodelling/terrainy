# terrainy

A downloader library for global terrain data and satellite imagery. It
will download a raster of global height data such as a DTM, or
satellite imagery for a polygon.


# Example usage

A more detailed usage guide is available in the [example usage
notebook](docs/Example usage.ipynb).

`import terrainy`

Load the shapefile you'd like to get a terrain surface for and convert its coordinates to WGS84 / EPSG:4326:

```
df = gpd.read_file("some_area_of_interest_polygon.shp").to_crs("EPSG:4326")
```

To see what data terrainy has available for your shapefile

```
print(terrainy.get_maps(df))
```

Download from a DTM of Norway at 1m resolution and export as a GeoTIFF
file:

```
data_dict = terrainy.download(df, "Norway DTM", 1)
terrainy.export(data_dict, "dtm_for_some_area.tif"))
```

