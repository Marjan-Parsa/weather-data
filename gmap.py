import numpy as np
import pandas as pd
import pandas_profiling as pp
import requests
from bokeh.io import output_file, show
from bokeh.models import ColorBar, ColumnDataSource, GMapOptions, HoverTool
from bokeh.palettes import Plasma256 as palette
from bokeh.plotting import gmap
from bokeh.transform import linear_cmap

API_ENDPOINT = 'https://maps.googleapis.com/maps/api/geocode/json?address='
API_KEY = "xxx"

output_file("output/gmap.html")


def _make_df():
    # Load data
    df = pd.read_csv('output/city-temperature.cvs')
    df['radius'] = np.sqrt(df['max'])*3.
    df.head()
    df.shape
    return df


def display_in_map(lat, lng, zoom=3, map_type='roadmap'):
    df = _make_df()
    gmap_options = GMapOptions(lat=lat, lng=lng, map_type=map_type, zoom=zoom)

    hover = HoverTool(
        tooltips = [
            ('name', '@city name'),
        ]
    )

    p = gmap(API_KEY, gmap_options, title='Temperature information', sizing_mode="stretch_both",
             tools=[hover, 'reset', 'wheel_zoom', 'pan'])

    source = ColumnDataSource(df)
    mapper = linear_cmap('max', palette, -20., 40.)
    center = p.circle('lon', 'lat', alpha=0.6, size='radius', color=mapper, source=source)
    color_bar = ColorBar(color_mapper=mapper['transform'], location=(0, 0))
    p.add_layout(color_bar, 'right')
    show(p)
    return p


def display_in_table():
    df = _make_df()
    df["date"] = pd.to_datetime(df["date"])
    profile = pp.ProfileReport(df, title = "Temperature Exploration")
    # profile.to_notebook_iframe()
    profile.to_file("output/table.html")


def get_geo_data_by_name(city_name):
    url = f'{API_ENDPOINT}address={city_name}&key={API_KEY}'
    response = requests.get(url)
    geo_data = response.json()['results'][0]
    return geo_data['geometry']['location']['lat'], geo_data['geometry']['location']['lng']
