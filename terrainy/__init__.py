import rasterio
from rasterio import MemoryFile
import rasterio.mask
from rasterio.transform import Affine
import geopandas as gpd
import time
import numpy as np
from shapely.geometry import Polygon
from owslib.wcs import WebCoverageService
from terrainy.countries import countries


def wcs_connect(wcs_service, version):
    wcs = WebCoverageService(wcs_service, version=version)
    return wcs

def getDTM(country, area_shape, tif_res, out_path):
    wcs = wcs_connect(countries[country][0], countries[country][1])
    shapefile = gpd.read_file(area_shape)

    if shapefile.crs == "EPSG:25833":
        print('Working on getting your data..')
        xmin, ymin, xmax, ymax = shapefile.total_bounds

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
                    crs="EPSG:25833",
                    bbox=polygon.bounds,
                    resx=tif_res, resy=tif_res,
                    format='GeoTIFF')

                with MemoryFile(response) as memfile:
                    with memfile.open() as dataset:
                        data_array = dataset.read()

                        array[y_idx * tile_pixel_width:y_idx * tile_pixel_width + tile_pixel_width,
                        x_idx * tile_pixel_length:x_idx * tile_pixel_length + tile_pixel_length] = data_array[0, :, :]


        transform = Affine.translation(xmin, ymax) * Affine.scale(tif_res, -tif_res)
        ras_meta = {'driver': 'GTiff',
                    'dtype': 'float32',
                    'nodata': None,
                    'width': array.shape[1],
                    'height': array.shape[0],
                    'count': 1,
                    'crs': "EPSG:25833",
                    'transform': transform,
                    'tiled': False,
                    'interleave': 'band'}

        print('Finished packaging data, exporting...')

    else:
        print('Shapefile CRS is %s, please load one in epsg:25833' % (shapefile.crs))

    with rasterio.open(out_path, 'w', **ras_meta) as tif:
        tif.write(array, indexes=1)

    print("Data successfully downloaded!")




