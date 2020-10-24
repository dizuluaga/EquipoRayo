import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from datetime import timedelta
from plotly.subplots import make_subplots
from datetime import datetime as dt
import json
import numpy as np
import pandas as pd
import os
import geopandas as gpd

from app import app
import data.data_import as di
import lib.buffer as buf

discharges = di.discharges
towers = di.towers
outages = di.outages
discharges_all_outages = di.discharges_all_outages

mapbox_token = 'pk.eyJ1IjoiZGlhbmFwenA5NiIsImEiOiJja2dlNTUxbWExN2VkMnJxdTdpYmxrcWowIn0.BaVVonTGXIQavJojx-v4sw'
mapstyle = 'mapbox://styles/dianapzp96/ckgijhjph0h3x19pfx3fpo5na'

# #################################################################################
# Here the layout for the plots to use.
#################################################################################
stats = html.Div(
    [
        html.Div([
            dcc.Graph(id="fig-id", style={
                'width': '100%',
                'height': '650%'
            })
        ]),
        dbc.Row([
            dbc.Col(
                html.Label(children='Select value to display:',
                           id='polarity-label')),
            dbc.Col(
                html.Label(children='Enter distance to buffer:',
                           id='buffer-label'))
        ]),
        dbc.Row([
            dbc.Col(
                dcc.Dropdown(id='polatiry_or_magnitude',
                             options=[{
                                 'label': i,
                                 'value': i
                             } for i in ['polarity', 'magnitude', 'current']],
                             value='magnitude')),
            dbc.Col(
                dcc.Input(id='buffer_input',
                          placeholder='kilometers:',
                          type='text',
                          value='5'))
        ]),
        html.Div([
            html.Label(children='From 2007 to 2017 minutes before outage',
                       id='time-range-label'),
            dcc.RangeSlider(id='year_slider',
                            min=0,
                            max=30,
                            step=1,
                            marks={i: f'{i}'
                                   for i in range(30)},
                            value=[5, 10])
        ]),
        html.Div([
            dcc.Dropdown(
                id='time_series_id',
                options=[{
                    'label': 'Magnitud',
                    'value': 'magnitude'
                }, {
                    'label': 'Current',
                    'value': 'current'
                }, {
                    'label': 'Polarity',
                    'value': 'polarity'
                }],
                multi=True,
                value=['magnitude'],
            )
        ]),
        dcc.Graph(id="line-fig"),
    ],
    className="ds4a-body",
)


@app.callback(output=Output(component_id='polarity-label',
                            component_property='children'),
              inputs=[
                  Input(component_id='polatiry_or_magnitude',
                        component_property='value')
              ])
def _update_label(label_selected):
    return 'Select value to display: {}'.format(label_selected)


@app.callback(
    output=Output(component_id='time-range-label',
                  component_property='children'),
    inputs=[Input(component_id='year_slider', component_property='value')])
def _update_time_range_label(year_range):
    return 'From {} to {} minutes before outage'.format(
        year_range[0], year_range[1])


@app.callback(
    output=[Output('fig-id', 'figure'),
            Output('line-fig', 'figure')],
    inputs=[
        Input(component_id='year_slider', component_property='value'),
        Input('outage_dropdown', 'value'),
        Input('polatiry_or_magnitude', 'value'),
        Input('buffer_input', 'value'),
        Input('time_series_id', 'value')
    ],
)
def _update_graph(year_range, outage_indicator, polatiry_or_magnitude,
                  buffer_dist, input_values):
    # print(year_range)
    print(input_values)
    # print(polatiry_or_magnitude)
    # print(outages.loc[outage_indicator, 'date'])
    outage_date = outages.loc[outage_indicator, 'date']
    min_start = year_range[0]
    min_end = year_range[1]
    discharges_outage_1 = di.Discharges_before_outage_by_time(
        outage_date, min_end, min_start)
    discharges_outage_1.sort_values(polatiry_or_magnitude, inplace=True)

    discharges_outage_1=gpd.GeoDataFrame(discharges_outage_1,\
         geometry=gpd.points_from_xy(discharges_outage_1.longitude, discharges_outage_1.latitude))

    if not buffer_dist:
        buffer_dist = '10'
    # print(buffer_dist)
    lon_x, lon_y, gdf_buffer = buf.buffer_line(float(buffer_dist))
    discharges_outage_1 = discharges_outage_1.loc[discharges_outage_1.within(
        gdf_buffer.geometry.iloc[0])]

    map_fig = go.Figure()
    map_fig.add_trace(
        go.Scattermapbox(
            lat=discharges_outage_1.latitude,
            lon=discharges_outage_1.longitude,
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=7,
                color=discharges_outage_1[polatiry_or_magnitude],
                colorscale=None
                if polatiry_or_magnitude != 'polarity' else ['red', 'blue'],
                opacity=0.7,
                showscale=False
                if polatiry_or_magnitude == 'polarity' else True,
                colorbar=dict(title=polatiry_or_magnitude),
            ),
            text=discharges_outage_1[polatiry_or_magnitude],
            hovertemplate=polatiry_or_magnitude + ': %{text:.2f}',
            hoverinfo='text',
            name="Discharges",
        ))
    map_fig.add_trace(
        go.Scattermapbox(
            lat=towers.latitude,
            lon=towers.longitude,
            mode='markers',  #markers+lines
            marker=go.scattermapbox.Marker(size=7, color='black', opacity=0.7),
            name="Towers"))

    map_fig.add_trace(
        go.Scattermapbox(lon=np.array(lon_x),
                         lat=np.array(lon_y),
                         mode="lines",
                         name=f'{buffer_dist}km buffer',
                         marker=go.scattermapbox.Marker(
                             size=8, color='rgb(242, 177, 172)', opacity=0.3)
                         #inherit=False
                         ))

    map_fig.update_layout(
        title='Electric discharges of the last 20 minutes',
        legend=dict(x=0.025, y=.95),
        autosize=True,
        height=700,
        showlegend=True,
        # hovermode='closest',
        # mapbox_style="open-street-map",
        mapbox=dict(
            accesstoken=mapbox_token,
            style=mapstyle,
            #    bearing=0,
            center=dict(lat=6.73, lon=-73.9),
            zoom=9))

    #map_fig.add_area(buf.buffer_3km_json['coordinates'])
    map_fig['layout']['uirevision'] = 'no reset of zoom'

    ###################################
    df = discharges_outage_1.copy()
    # Add traces
    line_fig = make_subplots(rows=1, cols=len(input_values))
    # Add traces
    for i, variable in enumerate(input_values):
        line_fig.add_trace(
            go.Scatter(
                x=df.date,
                y=df[variable],
                mode='markers',
                # mode='markers+lines',
                name=variable,
            ),
            row=1,
            col=i + 1)

    line_fig.update_layout(
        shapes=[
            # 1st highlight during Feb 4 - Feb 6
            dict(
                type="line",
                # x-reference is assigned to the x-values
                xref=f"x{i}",
                # y-reference is assigned to the plot paper [0,1]
                yref="paper",
                x0=outage_date,
                y0=0,
                x1=outage_date,
                y1=1,
                fillcolor="LightSalmon",
                opacity=0.5,
                layer="above",
                line=dict(
                    color="red",
                    width=4,
                )) for i in range(1,
                                  len(input_values) + 1)
        ],
        annotations=[
            dict(x=outage_date,
                 y=0.5,
                 showarrow=False,
                 text="Outage",
                 xref=f"x{i}",
                 yref="paper",
                 textangle=270,
                 xshift=-15,
                 font=dict(family="sans serif", size=20, color="crimson"))
            for i in range(1,
                           len(input_values) + 1)
        ],
    )
    line_fig.update_xaxes(matches='x')
    if len(input_values) == 1:
        line_fig.update_yaxes(title=input_values[0])
    # line_fig['layout']['uirevision'] = 'no reset of zoom'

    return map_fig, line_fig
