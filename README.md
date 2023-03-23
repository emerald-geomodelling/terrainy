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
terrainy.export(data_dict,
                out_path=filename,
                out_crs=projection,
                crop_geom=shape,
                crop_geom_crs=projection,
                buffer=buffer,
                driver="PNG")
```
where: 
```
out_crs = EPSGC code: int, crs to convert the tif or png  too, e.g. 25833
crop_geom = shapely geometry object to crop the tif or png too
crop_geom_crs = EPSG code: int, crs of shapely geom object, e.g. 25833
buffer = int, if you want to buffer your cropping in (e.g. 10 or -10)
driver = str, geotiff by default, but for satellite imagery (e.g. for textures), set as PNG
```
