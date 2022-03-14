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
# @click.option('--informat', default="sgf", help='Input format: %s' % ", ".join(parsers.keys()))
# @click.option('--outformat', default="sgf", help='Ouput format: %s' % ", ".join(dumpers.keys()))
# @click.argument('input', type=str)
# @click.argument('output', type=str)
def list():
    s = sources.load()
    s = s.join(s.geometry.bounds)

    s = s.drop(columns=["connection_args", "geometry"])

    print(s)
    
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

