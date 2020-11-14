import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from datetime import timedelta
from plotly.subplots import make_subplots
from datetime import datetime as dtm
import json
import numpy as np
import pandas as pd
import os
import geopandas as gpd
import geopandas as gpd
from shapely.geometry import LineString, Point
from dash.exceptions import PreventUpdate
from app import app
import lib.buffer as buf

from lib import stats

# discharges = di.discharges
# towers = di.towers
# outages = di.outages

def get_frames(minutes_animation, outage_date, variable='magnitude', discharges = None):
    frames = []
    for i in range(minutes_animation + 1):
        discharges_before = stats.Discharges_before_outage_by_time(
            outage_date, 1, min_before=20 - i, discharges= discharges
        )
        frames.append(
            go.Frame(
                data=[
                    go.Scattermapbox(
                        lat=discharges_before.latitude,
                        lon=discharges_before.longitude,
                        texttemplate = "Longitude: %{lon:$.2f}, Longitude: %{lat:$.2f}",
                        marker=go.scattermapbox.Marker(
                            size=7,
                            color=discharges_before[variable],
                            colorscale=None,
                            opacity=0.7,
                            showscale=False,
                            colorbar=dict(title="lll"),
                        ),
                        customdata=pd.concat(
                            [
                                discharges_before.date.dt.strftime("%H:%M:%S"),
                                discharges_before.magnitude,
                                discharges_before.polarity,
                                discharges_before.current,
                            ],
                            axis=1,
                        ).values,
                        hovertemplate="<b>Time: %{customdata[0]}</b><br><br>Magnitude: %{customdata[1]:.1f}</b><br>Polarity: %{customdata[3]:.0f}",
                    ),
                ],
                name=f"frame{i}",
            )
        )
    return frames


def get_figure(outage_index, variable_to_show, outages  =None, towers= None, discharges = None, centroid=None):
    outage_date = outages.loc[outage_index, "date"]
    minutes_animation = 35

    frames = get_frames(minutes_animation, outage_date,variable_to_show, discharges=discharges)
    df = stats.Discharges_before_outage_by_time(outage_date, 1, min_before=minutes_animation, discharges=discharges)

    fig = go.Figure(
        go.Scattermapbox(
            lat=df.latitude,
            lon=df.longitude,
            mode="markers",
        )
    )

    fig.add_trace(
        go.Scattermapbox(
            lat=towers.latitude,
            lon=towers.longitude,
            mode="markers",  # markers+lines
            marker=go.scattermapbox.Marker(size=7, color="black", opacity=0.7),
            name="Towers",
        )
    )
    fig.update(layout_showlegend=False)
    fig.update_layout(
        margin={"t": 0.2, "l": 0, "b": 0},
        height=700,
        mapbox=dict(  # accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(lat=centroid[1], lon=centroid[0]),
            pitch=0,
            zoom=9,
            style="carto-positron",
        ),
    )

    fig.update(frames=frames)
    sliders = [
        dict(
            steps=[
                dict(
                    method="animate",
                    args=[
                        [f"frame{k}"],
                        dict(
                            mode="immediate",
                            frame=dict(duration=100, redraw=True),
                            transition=dict(duration=0),
                            label="C",
                        ),
                    ],
                    label="{:d}".format(k),
                )
                for k in range(len(frames))
            ],
            transition=dict(duration=0),
            x=0.1,  # slider starting position
            y=0,
            len=0.9,
            ticklen=3,
            pad={"b": 10, "t": 0},
            font={"size": 10},
            currentvalue=dict(
                font=dict(size=12), prefix="Minute: ", visible=True, xanchor="center"
            ),
        )
    ]

    fig["layout"]["updatemenus"] = [
        {
            "buttons": [
                {
                    "args": [
                        None,
                        {
                            "frame": {"duration": 500, "redraw": True},
                            "fromcurrent": True,
                            "transition": {"duration": 0, "easing": "quadratic-in-out"},
                        },
                    ],
                    "label": "Play",
                    "method": "animate",
                },
                {
                    "args": [
                        [None],
                        {
                            "frame": {"duration": 0, "redraw": True},
                            "mode": "immediate",
                            "transition": {"duration": 0},
                        },
                    ],
                    "label": "Pause",
                    "method": "animate",
                },
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 20},
            "showactive": False,
            "type": "buttons",
            "x": 0.1,
            "xanchor": "right",
            "y": 0,
            "yanchor": "top",
        }
    ]

    fig["layout"]["sliders"] = sliders
    
    return fig


@app.callback(
    Output("fig-id-animated", "figure"),
    [
        Input("tabs-example", "value"),
        Input("outage_dropdown", "value"),
        Input("polatiry_or_magnitude", "value"),
        Input("memory-towers", "data"),
        Input("memory-discharges", "data"),
        Input("memory-outages", "data"),
    ],
)
def render_content(tab, outage, variable,data_towers, data_discharges, data_outages,):
    towers = pd.DataFrame.from_dict(data_towers)
    towers = gpd.GeoDataFrame(towers,
                          geometry=gpd.points_from_xy(towers.longitude,
                                                      towers.latitude),
                          crs='EPSG:4326')
    towers_line= LineString(towers["geometry"])
    towers_line = gpd.GeoDataFrame(geometry=[towers_line], crs="EPSG:4326")
    outages = pd.DataFrame.from_dict(data_outages)
    discharges = pd.DataFrame.from_dict(data_discharges)
    # print('outages',outages.head(2))
    outages['date'] = pd.to_datetime(outages['date'])
    discharges['date'] = pd.to_datetime(discharges['date'])
    outage_date = outages.loc[int(outage), "date"]
    centro = towers_line.centroid
    x = centro.x.iloc[0]
    y = centro.y.iloc[0]
    print('outages animated', discharges.head(1))
    if tab == "tab-2":
        return get_figure(int(outage), variable, outages=outages, towers=towers, discharges=discharges, centroid=(x,y))
    else:
        raise PreventUpdate
