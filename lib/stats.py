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

from app import app
import data.data_import as di
import lib.buffer as buf
import lib.animated

discharges = di.discharges
towers = di.towers
outages = di.outages

discharges_all_outages = pd.DataFrame(columns=discharges.columns)

available_indicators = outages.index


def Discharges_before_outage_by_time(
    outage_date, time_range, min_before=5, discharges=None
):
    datetime_f = outage_date - timedelta(minutes=min_before)
    datetime_i = datetime_f - timedelta(minutes=time_range)
    discharges_copy = discharges.copy()
    discharges_before_outage_by_time = discharges_copy[
        (discharges["date"] > datetime_i) & (discharges_copy["date"] < datetime_f)
    ].reset_index()
    return discharges_before_outage_by_time


mapbox_token = "pk.eyJ1IjoiZGlhbmFwenA5NiIsImEiOiJja2dlNTUxbWExN2VkMnJxdTdpYmxrcWowIn0.BaVVonTGXIQavJojx-v4sw"
mapstyle = "mapbox://styles/dianapzp96/ckgijhjph0h3x19pfx3fpo5na"

# #################################################################################
# Here the layout for the plots to use.
#################################################################################
# 1,2,3
lineas_dict = {
    "comuneros": "Comuneros Primavera",
    "cerromatoso": "Cerromatoso Primavera",
    "virginia": "La Virginia San Carlos",
}
lineas_dict_numbers = {
    "comuneros": 1,
    "cerromatoso": 2,
    "virginia": 3,
}

title = html.Div(
    className="ds4a-title",
    children=[
        dbc.Row(
            dbc.Col(
                html.H3(id="title-id"),
                width={"color": "#F8F9F9"},
            ),
            justify="left",
            align="center",
            className="h-50",
        )
    ],
    id="title",
)
layout = html.Div(
    [
        title,
        html.Div(
            [
                dcc.Tabs(
                    id="tabs-example",
                    value="tab-1",
                    children=[
                        dcc.Tab(
                            label="Principal",
                            value="tab-1",
                            children=[
                                dcc.Loading(
                                    children=[
                                        dcc.Graph(
                                            id="fig-id",
                                            style={"width": "100%", "height": "650%"},
                                            config={"displayModeBar": False},
                                        )
                                    ],
                                    color="#119DFF",
                                    type="dot",
                                    fullscreen=False,
                                )
                            ]
                        ),
                        dcc.Tab(
                            label="Animated",
                            value="tab-2",
                            # children=[html.Div(id="tabs-example-content")],
                            children=dcc.Graph(
                                id="fig-id-animated",
                                style={"width": "100%", "height": "650%"},
                                config={"displayModeBar": False},
                            ),
                        ),
                    ],
                    persistence=True
                ),
            ]
        ),
        # [dcc.Graph(id="fig-id", style={"width": "100%", "height": "650%"})]),
        dbc.Row(
            [
                dbc.Col(
                    html.Label(children="Select power line:", id="power-line-label")
                ),
                dbc.Col(html.Label(children="Select outage:", id="outage-label")),
                dbc.Col(
                    html.Label(children="Select value to display:", id="polarity-label")
                ),
                dbc.Col(
                    html.Label(children="Enter distance to buffer:", id="buffer-label"),
                    width=None,
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Dropdown(
                        id="power_line_name",
                        options=[
                            {"label": lineas_dict[i], "value": i}
                            for i in lineas_dict.keys()
                        ],
                        value="comuneros",
                    )
                ),
                dbc.Col(
                    dcc.Loading(
                        id="loading-1",
                        type="default",
                        children=[
                            dcc.Dropdown(
                                id="outage_dropdown",
                                options=[
                                    {
                                        "label": f"{num+1}: "
                                        + outages.loc[i, "date"].strftime("%Y-%m-%d"),
                                        "value": i,
                                    }
                                    for num, i in enumerate(available_indicators)
                                ],
                                value="103",
                                multi=False,
                            )
                        ],
                    )
                ),
                dbc.Col(
                    dcc.Dropdown(
                        id="polatiry_or_magnitude",
                        options=[
                            {"label": i, "value": i}
                            for i in ["polarity", "magnitude", "current"]
                        ],
                        value="magnitude",
                    )
                ),
                dbc.Col(
                    dcc.Input(
                        id="buffer_input",
                        placeholder="kilometers:",
                        type="number",
                        value=15,
                        min=0,
                    ),
                    width=None,
                ),
            ]
        ),
        html.Div(
            [
                html.Label(
                    children="From 2007 to 2017 minutes before outage",
                    id="time-range-label",
                ),
                dcc.RangeSlider(
                    id="year_slider",
                    min=0,
                    max=30,
                    step=1,
                    marks={i: f"{i}" for i in range(30)},
                    value=[5, 10],
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label(children="Showing:", id="select_label"),
                        dcc.Dropdown(
                            id="time_series_id",
                            options=[
                                {"label": "Magnitud", "value": "magnitude"},
                                {"label": "Current", "value": "current"},
                                {"label": "Polarity", "value": "polarity"},
                            ],
                            multi=True,
                            clearable =False,
                            value=["magnitude"],
                        ),
                    ]
                ),
                dbc.Col(
                    [
                        html.Label(children="Resampling:", id="resample"),
                        dcc.RadioItems(
                            id="yes_no",
                            options=[
                                {"label": "No", "value": "no"},
                                {"label": "Yes", "value": "yes"},
                            ],
                            className="my_box_container",
                            labelClassName="my_box_label",
                            value="no",
                            labelStyle={"display": "inline-block"},
                        ),
                    ]
                ),
                dbc.Col(
                    [
                        html.Label(children="How:", id="resampling_method"),
                        dcc.Dropdown(
                            id="resampling_dropdown",
                            options=[
                                {"label": "Mean", "value": "mean"},
                                {"label": "Max", "value": "max"},
                                {"label": "Min", "value": "min"},
                                {
                                    "label": "Conteo",
                                    "value": "count",
                                },
                            ],
                            multi=False,
                            value="mean",
                        ),
                    ]
                ),
                dbc.Col(
                    [
                        html.Label(children="Frecuency:", id="resampling_time_label"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Dropdown(
                                        id="resampling_time_number",
                                        options=[
                                            {"label": i, "value": i}
                                            for i in range(0, 20)
                                        ],
                                        multi=False,
                                        value=1,
                                    )
                                ),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id="resampling_time_label",
                                        options=[
                                            {"label": "Minutes", "value": "min"},
                                            {"label": "Seconds", "value": "S"},
                                        ],
                                        multi=False,
                                        value="min",
                                    )
                                ),
                            ]
                        ),
                    ]
                ),
            ]
        ),
        dcc.Graph(id="line-fig", config=dict(scrollZoom=True)),
    ],
    className="ds4a-body",
)

# @app.callback(
#     Output('outage_dropdown', 'options'),
#     [Input('power_line_name', 'value'),
#      Input('memory-discharges', 'data')])
# def set_cities_options(selected_country):
#     towers =  pd.DataFrame.from_dict(data)
#     return [{'label': i, 'value': i} for i in all_options[selected_country]]


@app.callback(
    output=Output(component_id="polarity-label", component_property="children"),
    inputs=[Input(component_id="polatiry_or_magnitude", component_property="value")],
)
def _update_label(label_selected):
    return "Select value to display: {}".format(label_selected)


# TODO Change title
@app.callback(
    output=[
        Output(component_id="title-id", component_property="children"),
        Output("outage_dropdown", "options"),
    ],
    inputs=[
        Input(component_id="power_line_name", component_property="value"),
        Input("memory-outages", "data"),
    ],
)
def _update_time_range_label(power_line, data_outages):
    title_towers = "{} Power Line".format(lineas_dict[power_line])

    outages = pd.DataFrame.from_dict(data_outages)
    outages["date"] = pd.to_datetime(outages["date"])
    print('updating dropdown')
    options_dropdown = [
        {
            "label": f"{num+1}: " + outages.loc[i, "date"].strftime("%Y-%m-%d"),
            "value": i,
        }
        for num, i in enumerate(outages.index)
    ]
    return title_towers, options_dropdown


# @app.callback(Output("outage_dropdown", "value"), [Input("outage_dropdown", "options")])
# def set_cities_value(available_options):
#     return available_options[0]["value"]


@app.callback(
    output=Output(component_id="time-range-label", component_property="children"),
    inputs=[Input(component_id="year_slider", component_property="value")],
)
def _update_time_range_label(year_range):
    return "From {} to {} minutes before outage".format(year_range[0], year_range[1])


@app.callback(
    output=[Output("fig-id", "figure"), Output("line-fig", "figure"), Output('confirm', 'displayed')],
    inputs=[
        Input(component_id="year_slider", component_property="value"),
        Input("outage_dropdown", "value"),
        Input("polatiry_or_magnitude", "value"),
        Input("buffer_input", "value"),
        Input("time_series_id", "value"),
        Input("yes_no", "value"),
        Input("resampling_dropdown", "value"),
        Input("resampling_time_number", "value"),
        Input("resampling_time_label", "value"),
        Input("memory-towers", "data"),
        Input("memory-discharges", "data"),
        Input("memory-outages", "data"),
    ],
)
def _update_graph(
    year_range,
    outage_indicator,
    polatiry_or_magnitude,
    buffer_dist,
    input_values,
    yes_no_value,
    resampling_dropdown,
    resampling_time_number,
    resampling_time_label,
    data_towers,
    data_discharges,
    data_outages,
):
    towers = pd.DataFrame.from_dict(data_towers)
    outages = pd.DataFrame.from_dict(data_outages)
    discharges = pd.DataFrame.from_dict(data_discharges)
    if discharges.empty:
        print('emptyyyyy')
        return dash.no_update, dash.no_update, True
 
    else:
        print("outages", outages.head(2))
        outages["date"] = pd.to_datetime(outages["date"])
        discharges["date"] = pd.to_datetime(discharges["date"])
        print("Indicador", type(outage_indicator))
        outage_date = outages.loc[int(outage_indicator), "date"]
        print(outage_date)
        min_start = year_range[0]
        min_end = year_range[1]

        discharges_outage_1 = Discharges_before_outage_by_time(
            outage_date, min_end - min_start, min_start, discharges=discharges
        )
        print(min_end, min_start)
        discharges_outage_1.sort_values(polatiry_or_magnitude, inplace=True)
        discharges_outage_1 = gpd.GeoDataFrame(
            discharges_outage_1,
            geometry=gpd.points_from_xy(
                discharges_outage_1.longitude, discharges_outage_1.latitude
            ),
        )
        print(discharges_outage_1.head(2))
        if not buffer_dist:
            buffer_dist = 10
        # print(buffer_dist)
        lon_x, lon_y, gdf_buffer = buf.buffer_line(buffer_dist, towers_buffer=towers)
        discharges_outage_1 = discharges_outage_1.loc[
            discharges_outage_1.within(gdf_buffer.geometry.iloc[0])
        ]

        map_fig = go.Figure()
        map_fig.add_trace(
            go.Scattermapbox(
                lat=discharges_outage_1.latitude,
                lon=discharges_outage_1.longitude,
                mode="markers",
                marker=go.scattermapbox.Marker(
                    size=7,
                    color=discharges_outage_1[polatiry_or_magnitude],
                    colorscale=None
                    if polatiry_or_magnitude != "polarity"
                    else ["red", "blue"],
                    opacity=0.7,
                    showscale=False if polatiry_or_magnitude == "polarity" else True,
                    colorbar=dict(title=polatiry_or_magnitude),
                ),
                text=discharges_outage_1[polatiry_or_magnitude],
                hovertemplate=polatiry_or_magnitude + ": %{text:.2f}",
                hoverinfo="text",
                name="Discharges",
            )
        )
        map_fig.add_trace(
            go.Scattermapbox(
                lat=towers.latitude,
                lon=towers.longitude,
                mode="markers",  # markers+lines
                marker=go.scattermapbox.Marker(size=7, color="black", opacity=0.7),
                name="Towers",
                hovertemplate="longitude: %{lon:.2f}<br>" + "latitude: %{lat:.2f}<br>",
            )
        )

        map_fig.add_trace(
            go.Scattermapbox(
                lon=np.array(lon_x),
                lat=np.array(lon_y),
                mode="lines",
                name=f"{buffer_dist}km buffer",
                marker=go.scattermapbox.Marker(
                    size=8, color="rgb(242, 177, 172)", opacity=0.3
                )
            )
        )
        centro = gdf_buffer.centroid
        x = centro.x.iloc[0]
        y = centro.y.iloc[0]

        map_fig.update_layout(
            margin={"t": 0.2, "l": 0, "b": 10},
            legend=dict(x=0.025, y=0.97),
            autosize=True,
            height=500,
            showlegend=True,
            # hovermode='closest',
            # mapbox_style="open-street-map",
            mapbox=dict(
                accesstoken=mapbox_token,
                style=mapstyle,
                #    bearing=0,
                center=dict(lat=y, lon=x),
                zoom=9,
            ),
        )

        # map_fig.add_area(buf.buffer_3km_json['coordinates'])
        map_fig["layout"]["uirevision"] = "no reset of zoom"

        ###################################
        df = discharges_outage_1.copy()
        df.set_index("date", inplace=True)
        if yes_no_value == "yes":
            df = df.resample(
                f"{resampling_time_number}{resampling_time_label}",
                offset=f"{resampling_time_number}{resampling_time_label}",
            ).agg(resampling_dropdown)
        df.to_excel("ensayo_buscar.xlsx")
        # print("jol")
        df.dropna(inplace=True)
        # print(df)
        # Add traces
        line_fig = make_subplots(rows=1, cols=len(input_values))
        # Add traces
        for i, variable in enumerate(input_values):
            line_fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[variable],
                    mode="markers" if yes_no_value == "no" else "markers+lines",
                    # mode='markers+lines',
                    name=variable,
                ),
                row=1,
                col=i + 1,
            )

        line_fig.update_layout(
            margin={"t": 5, "l": 0, "b": 10, 'r':0},
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
                    ),
                )
                for i in range(1, len(input_values) + 1)
            ],
            annotations=[
                dict(
                    x=outage_date,
                    y=0.5,
                    showarrow=False,
                    text="Outage",
                    xref=f"x{i}",
                    yref="paper",
                    textangle=270,
                    xshift=-15,
                    font=dict(family="sans serif", size=20, color="crimson"),
                )
                for i in range(1, len(input_values) + 1)
            ],
        )
        line_fig.update_xaxes(matches="x")
        if len(input_values) == 1:
            line_fig.update_yaxes(title=input_values[0])
        # line_fig['layout']['uirevision'] = 'no reset of zoom'
        print('figs updated')
        return map_fig, line_fig, dash.no_update
