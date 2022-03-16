import geopandas as gpd
import pandas as pd
import os.path
import pkg_resources
import traceback
from . import connection 

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

def add_source(**kw):
    con = connection.connect(**kw)
    kw["crs_orig"] = con.get_crs()
    kw["geometry"] = con.get_shape().to_crs(4326).iloc[0].geometry
    s = load()
    s.loc[kw.pop("title")] = kw
    dump(s)

def add_mapproxy(data):
    for title, spec in data["sources"].items():
        if "req" in spec and "url" in spec["req"]:
            try:
                add_source(
                    title=title,
                    connection_type = spec["type"],
                    connection_args = {"url": spec["req"]["url"]},
                    layer = spec["req"]["layers"])
            except Exception as e:
                print("Unable to add source %s/%s: %s: %s" % (
                    title, spec["req"]["layers"], spec["req"]["url"], e))
                traceback.print_exc()
