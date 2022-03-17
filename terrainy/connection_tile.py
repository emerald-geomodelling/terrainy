from . import connection
import contextily
import xyzservices.lib
import numpy as np
import geopandas as gpd
import shapely.geometry
from rasterio.transform import Affine

class TileConnection(connection.Connection):
    bands = 3
    dtype = "uint8"
    
    def __init__(self, **kw):
        connection.Connection.__init__(self, **kw)

        args = {"name": "", "attribution": ""}
        args.update(self.kw["connection_args"])
        
        self.source = xyzservices.lib.TileProvider(**args)

    def get_shape(self):
        return gpd.GeoDataFrame(geometry=[shapely.geometry.box(*self.get_bounds())], crs=self.get_crs())
        
    def download(self, gdf, tif_res):
        gdf = gdf.to_crs(self.get_crs())
        xmin, ymin, xmax, ymax = gdf.total_bounds

        world_bounds = self.get_bounds()

        # From definition of spherical mercator:
        # tif_res = (world_bounds[2] - world_bounds[0]) / (256 * 2**zoom)
        zoom = int(np.ceil(np.log2((world_bounds[2] - world_bounds[0]) / (256 * tif_res))))

        array, extent = contextily.bounds2img(xmin, ymin, xmax, ymax, ll=False, zoom=zoom, source=self.source)
        array = np.transpose(array, (2, 0, 1))

        left, right, bottom, top = extent
        xres = (right - left) / array.shape[1]
        yres = (top - bottom) / array.shape[2]
        
        transform = Affine.translation(left, top) * Affine.scale(xres, -yres)
        data = dict(self.kw)
        data["crs_orig"] = self.get_crs()
        return {"array":array, "transform":transform, "data":data, "gdf":gdf}

    def download_tile(self, bounds, tif_res, size):        
        raise NotImplementedError("Use download()")

    def get_bounds(self):
        # Lon,lat bbox: (-180, -85.051129, 180, 85.051129)
        return (-20037508.342789244, -20037508.342789255, 20037508.342789244, 20037508.342789244)

    def get_crs(self):
        return 3857
