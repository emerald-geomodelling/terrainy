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
import importlib.metadata
import shapely
import json

# Grid sizing
tile_pixel_length = 1024
tile_pixel_width = 1024

class Connection(object):
    def __init__(self, **kw):
        self.kw = kw

    def get_shape(self):
        bbox = self.get_bounds()
        response = self.download_tile(bbox,
                                      (bbox[2] - bbox[0]) / tile_pixel_width,
                                      (tile_pixel_width, tile_pixel_length))

        with MemoryFile(response) as memfile:
            with memfile.open() as dataset:
                data_array = dataset.read()
        
        geometry = [shapely.geometry.shape(shp)
                    for shp, val in rasterio.features.shapes((data_array != 0).astype("int16"), transform=dataset.transform)
                    if val > 0]
        
        return gpd.GeoDataFrame(
            geometry = [gpd.GeoDataFrame(geometry = geometry).geometry.unary_union]
        ).set_crs(self.get_crs())

    def download(self, gdf, tif_res):
        # Convert data back to crs of map
        gdf = gdf.to_crs(self.get_crs())
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


def connect(**data):
    connections = {entry.name: entry.load()
               for entry in importlib.metadata.entry_points()['terrainy.connection']}
    if data["connection_type"] not in connections:
        raise NotImplementedError("Unknown connection type")
    return connections[data["connection_type"]](**data)
