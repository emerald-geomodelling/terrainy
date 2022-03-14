import geopandas as gpd
import pandas as pd
import os.path
import pkg_resources

sources_path = os.path.expanduser("~/.config/terrainy/sources.geojson")

def load():
    with pkg_resources.resource_stream("terrainy", "terrainy_datasource_20210930.geojson") as f:
        sources = gpd.read_file(f).set_index("title")
    if os.path.exists(sources_path):
        with open(sources_path, "rb") as f:
            sources = pd.concat((
                sources,
                gpd.read_file(f).set_index("title"))
            )
    return sources.loc[~sources.index.duplicated(keep='first')]

def dump(sources):
    sources_dir = os.path.dirname(sources_path)
    if not os.path.exists(sources_dir):
        os.makedirs(sources_dir)
    sources.to_file(sources_path, driver='GeoJSON')
