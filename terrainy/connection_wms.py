from . import connection
from owslib.wms import WebMapService

class WmsConnection(connection.Connection):
    bands = 3
    dtype = "uint8"
    
    def __init__(self, **kw):
        connection.Connection.__init__(self, **kw)
        self.wms = WebMapService(**self.kw["connection_args"])
        self.layer = self.wms[self.kw["layer"]]

    def download_tile(self, bounds, tif_res, size):
        return self.wms.getmap(layers=[self.layer.id],
                               srs=self.get_crs(),
                               bbox=bounds,
                               size=size,
                               format='image/GeoTIFF')

    def get_bounds(self):
        return self.layer.boundingBox[:4]

    def get_crs(self):
        return self.layer.boundingBox[4]
