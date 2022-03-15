from . import connection
from owslib.wcs import WebCoverageService

class WcsConnection(connection.Connection):
    bands = 1
    dtype = "float64"
    
    def __init__(self, **kw):
        connection.Connection.__init__(self, **kw)
        self.wcs = WebCoverageService(**self.kw["connection_args"])
        self.layer = self.wcs[self.kw["layer"]]

    def download_tile(self, bounds, tif_res, size):
        return self.wcs.getCoverage(
            identifier=self.layer.id,
            crs=self.get_crs(),
            bbox=bounds,
            resx=tif_res, resy=tif_res,
            format='GeoTIFF')

    def get_bounds(self):
        return self.layer.boundingboxes[0]["bbox"]
        
    def get_crs(self):
        return self.layer.boundingboxes[0]["nativeSrs"]
