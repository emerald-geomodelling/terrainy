import rasterio
from rasterio import MemoryFile
import rasterio.mask
from rasterio.transform import Affine
import rasterio
from rasterio import MemoryFile
from rasterio.plot import show
import rasterio.mask
from rasterio.transform import Affine
from rasterio.crs import CRS
import geopandas as gpd
import time
import numpy as np
from shapely.geometry import Polygon
from owslib.wcs import WebCoverageService
import pkg_resources
import json

def _read_shp(f):
    return gpd.read_file(f)

with pkg_resources.resource_stream("terrainy", "terrainy_data.geojson") as f:
    terrainy_shp = _read_shp(f)

# Used to get the WCS service, can inspect contents of wcs
def wcs_connect(wcs_service, version):
    wcs = WebCoverageService(wcs_service, version=version)
    return wcs

# Returns the available map sources available from your input shapefile
def getMaps(gdf):
    result = terrainy_shp.loc[terrainy_shp.contains(gdf)]
    return result

# Returns the shape you want to use to get data from, based on the title
def chooseMap(title):
    return terrainy_shp.loc[terrainy_shp["title"]==title]

# Downloads the data from a given shapefile
def download(gdf, title, tif_res):
    data_dict = getDTM(gdf, title, tif_res)
    return data_dict

# Writes your file to a given output path
def export(data_dict, out_path):
    print('Packaging your data...')
    ras_meta = {'driver': 'GTiff',
                'dtype': 'float32',
                'nodata': None,
                'width': data_dict["array"].shape[1],
                'height': data_dict["array"].shape[0],
                'count': 1,
                'crs': data_dict["data"]["crs_orig"][0],
                'transform': data_dict["transform"],
                'tiled': False,
                'interleave': 'band'}

    with rasterio.open(out_path, 'w', **ras_meta) as tif:
        tif.write(data_dict["array"], indexes=1)

    print('Finished packaging data')


def getDTM(gdf, title, tif_res):
    data  = terrainy_shp.loc[terrainy_shp["title"]==title]

    #wcs = wcs_connect(**json.loads(data.loc[0]["connection"]))
    wcs = wcs_connect(data["connection"][0]["wcs_service"], version=data["connection"][0]["version"])

    print('Working on getting your data..')

    # Convert data back to WCS crs
    gdf = gdf.to_crs(data["crs_orig"][0])
    xmin, ymin, xmax, ymax = gdf.total_bounds

    # Grid sizing
    tile_pixel_length = 1024
    tile_pixel_width = 1024

    tile_m_length = tile_pixel_length * tif_res
    tile_m_width = tile_pixel_width * tif_res

    width = (xmax - xmin) / tif_res
    length = (ymax - ymin) / tif_res

    nr_cols = int(np.ceil(width / tile_pixel_length))
    nr_rows = int(np.ceil(length / tile_pixel_width))

    polygons = []

    array = np.zeros((tile_pixel_length * nr_rows, tile_pixel_width * nr_cols))

    for x_idx in range(nr_cols):
        for y_idx in range(nr_rows):
            print('Working on block %s,%s of %s,%s' % (x_idx + 1, y_idx + 1, nr_cols, nr_rows))

            x = xmin + x_idx * tile_m_width
            y = ymax - y_idx * tile_m_length - tile_m_length

            polygon = (Polygon(
                [(x, y), (x + tile_m_width, y), (x + tile_m_width, y + tile_m_length), (x, y + tile_m_length)]))

            c = wcs["dtm_25833"]

            response = wcs.getCoverage(
                identifier=c.id,
                crs=data["crs_orig"][0],
                bbox=polygon.bounds,
                resx=tif_res, resy=tif_res,
                format='GeoTIFF')

            with MemoryFile(response) as memfile:
                with memfile.open() as dataset:
                    data_array = dataset.read()

                    array[y_idx * tile_pixel_width:y_idx * tile_pixel_width + tile_pixel_width,
                    x_idx * tile_pixel_length:x_idx * tile_pixel_length + tile_pixel_length] = data_array[0, :, :]


    transform = Affine.translation(xmin, ymax) * Affine.scale(tif_res, -tif_res)
    print("Data successfully downloaded!")
    return {"array":array, "transform":transform, "data":data}









