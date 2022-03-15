import click
import pandas as pd
import geopandas as gpd
import json

from . import sources
from . import connection

pd.set_option('display.max_columns', None)
pd.set_option("display.max_rows", None)
pd.set_option('display.expand_frame_repr', False)

@click.group()
def main():
    pass

@main.group()
def source():
    pass

@source.command()
@click.option('--long', is_flag=True, default=False)
# @click.option('--outformat', default="sgf", help='Ouput format: %s' % ", ".join(dumpers.keys()))
# @click.argument('input', type=str)
# @click.argument('output', type=str)
def list(long=False):
    s = sources.load()
    #s = s.join(s.geometry.bounds)
    s["bbox"] = s.geometry.bounds.apply(lambda row: "%(minx).4f,%(miny).4f,%(maxx).4f,%(maxy).4f" % row, axis=1)
    
    s["url"] = s.connection_args.apply(lambda a: a["url"])
    s = s.drop(columns=["connection_args", "geometry"])

    maincols = ["layer", "connection_type", "url", "crs_orig", "bbox"]
    if long:
        cols = maincols + sorted(set(s.columns) - set(maincols))
    else:
        cols = maincols

    print(s[cols])
    
@source.command()
@click.argument('title', type=str)
@click.argument('connection_type', type=str)
@click.argument('connection_args', type=str)
@click.argument('layer', type=str)
def add(**kw):
    kw["connection_args"] = json.loads(kw["connection_args"])
    con = connection.connect(**kw)
    kw["crs_orig"] = con.get_crs()
    kw["geometry"] = con.get_shape().to_crs(4326).iloc[0].geometry
    s = sources.load()
    s.loc[kw.pop("title")] = kw
    sources.dump(s)

