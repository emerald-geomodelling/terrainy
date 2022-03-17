import rasterio
import rasterio.mask
from rasterio.transform import Affine
import rasterio
from rasterio import MemoryFile
from rasterio.plot import show
import rasterio.mask
from rasterio.transform import Affine
import rasterio.rio.clip
from rasterio.crs import CRS
import geopandas as gpd
import time
import numpy as np
from shapely.geometry import Polygon
from owslib.wcs import WebCoverageService
from owslib.wms import WebMapService
import pkg_resources
import shapely
import json

from . import connection
from . import sources
    
def download(gdf, title, tif_res):
    "Downloads raster data for a shape from a given source"
    data  = sources.load().loc[title]
    con = connection.connect(**data)
    return con.download(gdf, tif_res)

def clip_to_bounds(file, area):
    with rasterio.open(file) as src:
        bounds = shapely.geometry.box(**area.to_crs(src.crs).bounds.iloc[0].astype(int))
        out_image, out_transform = rasterio.mask.mask(src, [bounds], filled=False, crop=True)
        out_meta = src.meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform})
    with rasterio.open(file, "w", **out_meta) as dest:
        dest.write(out_image)
        
def export(data_dict, out_path):
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
    clip_to_bounds(out_path, data_dict["gdf"])


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








