import rasterio
import rasterio.mask
import rasterio
import rasterio.mask
from rasterio.transform import Affine
import rasterio.rio.clip

import geopandas as gpd
import pkg_resources
import shapely
from shapely.geometry import box, mapping
from rasterio.warp import calculate_default_transform, reproject, Resampling
import json

from . import connection
from . import sources

def connect(title):
    data  = sources.load().loc[title]
    data["title"] = data.name
    return connection.connect(**data)

def download(gdf, title, tif_res):
    "Downloads raster data for a shape from a given source"
    return connect(title).download(gdf, tif_res)

def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    return [json.loads(gdf.to_json())['features'][0]['geometry']]

def clip_to_area(file, area, to_bounds=True):
    with rasterio.open(file) as src:
        area = area.to_crs(src.crs)
        if to_bounds:
            clip = shapely.geometry.box(**area.bounds.iloc[0].astype(int))
        else:
            clip = area.geometry[0]
        out_meta = src.meta.copy()
        nodata = out_meta.get("nodata", None)
        if nodata is None: nodata = -10000
        out_image, out_transform = rasterio.mask.mask(src, [clip], filled=not to_bounds, crop=True, nodata=nodata)
    out_meta.update({
        "nodata": nodata,
        "driver": "GTiff",
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform})
    with rasterio.open(file, "w", **out_meta) as dest:
        dest.write(out_image)

def crop_raster(shape, filename, driver_type=None):
    """ Crops raster to given shape
        - shape: shapely.geometry object
        - filename: string, filepath, raster to read and save to
        - type: string, options: tif, png"""

    if driver_type:
        driver = driver_type
    else:
        driver = "GTiff"
    feature_coll = {
        "type": "FeatureCollection",
        "features": [
            {
                "id": "0",
                "type": "Feature",
                "properties": {"name": "Polygon"},
                "geometry": mapping(shape),
                "bbox": shape.bounds
            }
        ]
    }
    df = gpd.GeoDataFrame.from_features(feature_coll)

    shapes = getFeatures(df)

    with rasterio.open(filename) as src:
        out_image, out_transform = rasterio.mask.mask(src, shapes, nodata=-9999, crop=True)
        out_meta = src.meta
        out_meta.update({"driver": driver,
                         "height": out_image.shape[0],
                         "width": out_image.shape[1],
                         "transform": out_transform})

    with rasterio.open(filename, "w", **out_meta) as dest:
        dest.write(out_image)


def reproject_raster_to_project_crs(filename, out_crs):
    """ reproject an image to a new crs:
        inputs:
        filename: string, path to file to reproject
        out_crs: int, epsg code of destination crs"""
    dst_crs = ('EPSG:' + str(out_crs))

    with rasterio.open(filename) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        with rasterio.open(filename, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest)


def export(data_dict, out_path, out_crs=None, shape=None, crop=None, png=None):
    if png is True:
        ras_meta = {
            'driver': 'PNG',
            'height': data_dict["array"].shape[1],
            'width': data_dict["array"].shape[2],
            'count': 3,
            'crs': data_dict["data"]["crs_orig"],
            'dtype': data_dict["array"].dtype,
            'transform': data_dict["transform"],
            'nodata': 0
        }

        with rasterio.open(out_path, 'w', **ras_meta) as png:
            png.write(data_dict["array"][0:3])
        if crop is True:
            crop_raster(shape, out_path, driver_type="PNG")
        if out_crs:
            reproject_raster_to_project_crs(out_path, out_crs)

    else:
        ras_meta = {'driver': 'GTiff',
                    'dtype': data_dict["array"].dtype,
                    'nodata': None,
                    'width': data_dict["array"].shape[2],
                    'height': data_dict["array"].shape[1],
                    'count': data_dict["array"].shape[0],
                    'crs': data_dict["data"]["crs_orig"],
                    'transform': data_dict["transform"],
                    'tiled': False,
                    'interleave': 'band'}

        with rasterio.open(out_path, 'w', **ras_meta) as tif:
            tif.write(data_dict["array"])
        if crop is True:
            crop_raster(shape, out_path, driver_type="GTiff")
        if out_crs:
            reproject_raster_to_project_crs(out_path, out_crs)


def get_maps(gdf):
    "Returns the available map sources available from your input shapefile"
    s = sources.load()
    s = s.loc[s.geometry.is_valid]
    return s.loc[s.contains(gdf["geometry"][0])]

def choose_map(title):
    "Returns the shape you want to use to get data from, based on the title"
    s = sources.load()
    return s.loc[s["title"]==title]

# Legacy names
getMaps = get_maps
chooseMap = choose_map
getDTM = download
getImagery = download
export_terrain = export
export_imagery = export

    
# fixme: Make clipping work to actual shape
# def getFeatures(gdf):
#     """Function to parse features from GeoDataFrame in such a manner that rasterio wants them, from
#     https: // automating - gis - processes.github.io / CSC18 / lessons / L6 / clipping - raster.html"""
#     import json
#     return [json.loads(gdf.to_json())['features'][0]['geometry']]
#
# def clipTif(raster, shape):
#     # with fiona.open(clip_shape_, "r") as shapefile:
#     #     shapes = [feature["geometry"] for feature in shapefile]
#     #shapes = shape.geometry[0]
#
#     with rasterio.open(raster) as src:
#         out_image, out_transform = rasterio.mask.mask(src, shape, crop=True)
#         out_meta = src.meta
#
#     out_meta.update({"driver": "GTiff",
#                      "height": out_image.shape[1],
#                      "width": out_image.shape[2],
#                      "transform": out_transform})








