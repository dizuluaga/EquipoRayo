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
    [        html.Div(
            [
                dcc.Graph(id="fig-id",style = {'width': '100%', 'height':'650%'})
             ]
            ),html.Label(children='Select value to display:', id='polarity-label'),
     dcc.Dropdown(
                id='polatiry_or_magnitude',
                options=[{'label': i, 'value': i} for i in ['polarity','magnitude','current']],
                value='magnitude'
            ),
        html.Div([html.Label(children='From 2007 to 2017 minutes before outage', id='time-range-label'),dcc.RangeSlider(
                id='year_slider',
                min=0,
                max=30,
                step=1,
                marks={i:f'{i}' for i in range(30)},
                value=[5, 10])]),
         dcc.Graph(id="line-fig")
    ],
    className="ds4a-body",
)

# the value of RangeSlider causes Label to update
@app.callback(
    output=Output(component_id = 'polarity-label',component_property= 'children'),
    inputs=[Input(component_id = 'polatiry_or_magnitude', component_property='value')]
    )
def _update_label(label_selected):
    return 'Select value to display: {}'.format(label_selected)

@app.callback(
    output=Output(component_id = 'time-range-label',component_property= 'children'),
    inputs=[Input(component_id = 'year_slider', component_property='value')]
    )
def _update_time_range_label(year_range):
    return 'From {} to {} minutes before outage'.format(year_range[0], year_range[1])

# the value of RangeSlider causes Graph to update
@app.callback(
    output=[Output('fig-id', 'figure'),Output('line-fig', 'figure')],
    inputs=[Input(component_id = 'year_slider', component_property='value'),
            Input('outage_dropdown','value'),
            Input('polatiry_or_magnitude','value')
            ],
    )
def _update_graph(year_range, outage_indicator,polatiry_or_magnitude):
    print(year_range)
    print(polatiry_or_magnitude)
    print(outages.loc[outage_indicator,'date'])
    outage_date = outages.loc[outage_indicator,'date']
    min_start = year_range[0]
    min_end = year_range[1]
    discharges_outage_1 = di.Discharges_before_outage_by_time(outage_date, min_end,min_start)
    discharges_outage_1.sort_values(polatiry_or_magnitude, inplace = True)
    map_fig = go.Figure()
    map_fig.add_trace(go.Scattermapbox(
        lat=discharges_outage_1.latitude,
        lon=discharges_outage_1.longitude,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=7,
            color=discharges_outage_1[polatiry_or_magnitude],
            colorscale = None if polatiry_or_magnitude !='polarity' else ['red','blue'],
            opacity=0.7,
            showscale=False if polatiry_or_magnitude=='polarity' else True,
            colorbar=dict(title=polatiry_or_magnitude),
        ),
        text=discharges_outage_1[polatiry_or_magnitude],
        hovertemplate =polatiry_or_magnitude+': %{text:.2f}',
        hoverinfo='text',
        name="Discharges",
    ))
    map_fig.add_trace(go.Scattermapbox(
        lat=towers.latitude,
        lon=towers.longitude,
        mode='markers', #markers+lines
        marker=go.scattermapbox.Marker(
            size=7,
            color='black',
            opacity=0.7
        ),
        name="Towers"
    ))
    map_fig.add_trace(go.Scattermapbox(
        lon=np.array(buf.x_buffer_3km),
        lat=np.array(buf.y_buffer_3km),
        mode="lines",
        name='3km buffer',
        marker=go.scattermapbox.Marker(
            size=8,
            color='rgb(242, 177, 172)',
            opacity=0.3
        )
        #inherit=False
    ))
    map_fig.add_trace(go.Scattermapbox(
        lon=np.array(buf.x_buffer_5km),
        lat=np.array(buf.y_buffer_5km),
        mode="lines",
        name='5km buffer',
        marker=go.scattermapbox.Marker(
            size=8,
            color='rgb(142, 177, 172)',
            opacity=0.3
        )
        #inherit=False
    ))
    map_fig.update_layout(
        title='Electric discharges of the last 20 minutes',
        legend=dict(
        x=0.025,
        y=.95),
        autosize=True,
        height=700,
        showlegend=True,
        # hovermode='closest',
        # mapbox_style="open-street-map",
        mapbox=dict(
            accesstoken=mapbox_token,
            style=mapstyle,
        #    bearing=0,
            center=dict(
                lat=6.73,
                lon=-73.9
            ),
            zoom=9
    ))
    
    #map_fig.add_area(buf.buffer_3km_json['coordinates'])
    map_fig['layout']['uirevision'] = 'no reset of zoom'
    
    ###################################
    df = discharges_outage_1.copy()
    line_fig = go.Figure()
    # Add traces
    line_fig = make_subplots(rows=1, cols=3,  subplot_titles=('Magnitude','Current','Polarity'))
# Add traces
    line_fig.add_trace(go.Scatter(x=df.date, y=df.magnitude,
                        mode='markers',
                        name='markers'),row=1, col=1)
    line_fig.add_trace(go.Scatter(x=df.date, y=df.current,
                        mode='markers',
                        name='markers'),row=1, col=2,)
    line_fig.add_trace(go.Scatter(x=df.date, y=df.polarity,
                        mode='markers',
                        name='markers'),row=1, col=3,)
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
                )
            )
        for i in range(1,4)],
        annotations=[
            dict(
                x=outage_date,
                y=0.4,
                showarrow=False,
                text="Outage",
                xref=f"x{i}",
                yref="paper",
                textangle=270,
                xshift=-15,
                font=dict(
            family="sans serif",
            size=20,
            color="crimson"
        )
            ) for i in range(1,4)],
    )
    line_fig.update_xaxes(matches='x')
    line_fig['layout']['uirevision'] = 'no reset of zoom'
    
    return map_fig, line_fig
