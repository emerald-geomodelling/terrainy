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

# Grid sizing
tile_pixel_length = 1024
tile_pixel_width = 1024

def _read_shp(f):
    return gpd.read_file(f)

with pkg_resources.resource_stream("terrainy", "terrainy_datasource_20210930.geojson") as f:
    terrainy_shp = _read_shp(f).set_index("title")
        
class Connection(object):
    def __init__(self, **kw):
        self.kw = kw

    def download(self, gdf, tif_res):
        # Convert data back to crs of map
        gdf = gdf.to_crs(self.kw["crs_orig"])
        xmin, ymin, xmax, ymax = gdf.total_bounds

        tile_m_length = tile_pixel_length * tif_res
        tile_m_width = tile_pixel_width * tif_res

        width = (xmax - xmin) / tif_res
        length = (ymax - ymin) / tif_res

        nr_cols = int(np.ceil(width / tile_pixel_length))
        nr_rows = int(np.ceil(length / tile_pixel_width))

        array = np.zeros((self.bands, tile_pixel_length * nr_rows, tile_pixel_width * nr_cols), dtype=self.dtype)

        for x_idx in range(nr_cols):
            for y_idx in range(nr_rows):
                print('Working on block %s,%s of %s,%s' % (x_idx + 1, y_idx + 1, nr_cols, nr_rows))

                x = xmin + x_idx * tile_m_width
                y = ymax - y_idx * tile_m_length - tile_m_length

                polygon = (Polygon(
                    [(x, y), (x + tile_m_width, y), (x + tile_m_width, y + tile_m_length), (x, y + tile_m_length)]))

                response = self.download_tile(polygon.bounds, tif_res, (tile_pixel_width, tile_pixel_length))

                with MemoryFile(response) as memfile:
                    with memfile.open() as dataset:
                        data_array = dataset.read()

                        array[:, y_idx * tile_pixel_width:y_idx * tile_pixel_width + tile_pixel_width,
                        x_idx * tile_pixel_length:x_idx * tile_pixel_length + tile_pixel_length] = data_array[:, :, :]

        transform = Affine.translation(xmin, ymax) * Affine.scale(tif_res, -tif_res)
        return {"array":array, "transform":transform, "data":self.kw, "gdf":gdf}
    

class WcsConnection(Connection):
    bands = 1
    dtype = "float64"
    
    def __init__(self, **kw):
        Connection.__init__(self, **kw)
        self.wcs = WebCoverageService(**self.kw["connection_args"])
        self.layer = self.wcs[self.kw["layer"]]

    def download_tile(self, bounds, tif_res, size):
        return self.wcs.getCoverage(
            identifier=self.layer.id,
            crs=self.kw["crs_orig"],
            bbox=bounds,
            resx=tif_res, resy=tif_res,
            format='GeoTIFF')

class WmsConnection(Connection):
    bands = 3
    dtype = "uint8"
    
    def __init__(self, **kw):
        Connection.__init__(self, **kw)
        self.wms = WebMapService(**self.kw["connection_args"])
        self.layer = self.wms[self.kw["layer"]]

    def download_tile(self, bounds, tif_res, size):
        return self.wms.getmap(layers=[self.layer.id],
                               srs="EPSG:%s" % self.kw["crs_orig"],
                               bbox=bounds,
                               size=size,
                               format='image/GeoTIFF')

def download(gdf, title, tif_res):
    "Downloads raster data for a shape from a given source"
    data  = terrainy_shp.loc[title]
    if data.connection_type == "wcs":
        con = WcsConnection(**data)
    elif data.connection_type == "wms":
        con = WmsConnection(**data)
    else:
        raise NotImplementedError("Unknown connection type")
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


def getMaps(gdf):
    "Returns the available map sources available from your input shapefile"
    return terrainy_shp.loc[terrainy_shp.contains(gdf["geometry"][0])]

def chooseMap(title):
    "Returns the shape you want to use to get data from, based on the title"
    return terrainy_shp.loc[terrainy_shp["title"]==title]

def getDTM(gdf, title, tif_res):
    return download(gdf, title, tif_res)

def getImagery(gdf, title, tif_res):
    return download(gdf, title, tif_res)

def export_terrain(data_dict, out_path):
    export(data_dict, out_path)

def export_imagery(data_dict, out_path):
    export(data_dict, out_path)

    
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








