import json
from lib import buffer
import os
from datetime import datetime as dt
from dash_table.Format import Format, Group, Scheme, Symbol
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash_html_components import Div
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Recall app
import data.data_import_DB_L2
import real_time_app
# from real_time_app import discharges_by_cluster_df

from app import app
from dash.dependencies import ClientsideFunction, Input, Output, State
import dash_table
import lib.buffer as buf

from flask_caching import Cache

from lib.stats import mapbox_token
from lib.stats import mapstyle


alert = dbc.Alert(
    [
        html.H4("WARNING: Failure alert!", className="alert-heading"),
        html.P(
            "It is likely that in the next 5 minutes there will be a failure in the Comuneros-Primavera & Cerromatoso - Primavera power line."
        ),
        html.Hr(),
        html.P(
            "The probability must be higher than 30% for the cluster to be considered as a potential cause of failure.",
            className="mb-0",
        ),
    ],
    dismissable=True,
    id="alerta-message",
    is_open=True,
    duration=5000,
    color="danger",
)


cards_alerta = dbc.Row(
    [
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H5("Comuneros - Primavera"), style={"text-align": "center"}
                    ),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div(
                                            [
                                                html.H2("38.9%",
                                                    id="card-prob-1",
                                                    className="card-title",
                                                ),
                                                html.P(
                                                    "Probability of outage",
                                                    className="card-text",
                                                ),
                                            ],
                                        ),
                                        style={"text-align": "center"},
                                    ),
                                    dbc.Col(
                                        html.Div(
                                            [
                                                html.H2(
                                                    "2",
                                                    id="card-cellss",
                                                    className="card-clusters-1",
                                                ),
                                                html.P(
                                                    "discharge cells",
                                                    className="card-text",
                                                ),
                                            ]
                                        ),
                                        style={"text-align": "center"},
                                    ),
                                ]
                            )
                        ]
                    ),
                ],
                id="card-block",
            )
        ),
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H5("Cerromatoso - Primavera"),
                        style={"text-align": "center"},
                    ),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div(
                                            [
                                                html.H2(
                                                    "38.9%",
                                                    id="card-probability2",
                                                    className="card-title",
                                                ),
                                                html.P(
                                                    "Probability of outage",
                                                    className="card-text",
                                                ),
                                            ],
                                        ),
                                        style={"text-align": "center"},
                                    ),
                                    dbc.Col(
                                        html.Div(
                                            [
                                                html.H2(
                                                    "2",
                                                    id="card-clusters-2",
                                                    className="card-title",
                                                ),
                                                html.P(
                                                    "discharge cells",
                                                    className="card-text",
                                                ),
                                            ]
                                        ),
                                        style={"text-align": "center"},
                                    ),
                                ]
                            )
                        ]
                    ),
                ],
                id="card-block",
            )
        ),
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H5("San Carlos - La Virginia"),
                        style={"text-align": "center"},
                    ),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div(
                                            [
                                                html.H2(
                                                    "--",
                                                    id="card-probability-3",
                                                    className="card-title",
                                                ),
                                                html.P(
                                                    "Probability of outage",
                                                    className="card-text",
                                                ),
                                            ],
                                        ),
                                        style={"text-align": "center"},
                                    ),
                                    dbc.Col(
                                        html.Div(
                                            [
                                                html.H2(
                                                    "--",
                                                    id="card-clusters-3",
                                                    className="card-title",
                                                ),
                                                html.P(
                                                    "discharge cells",
                                                    className="card-text",
                                                ),
                                            ]
                                        ),
                                        style={"text-align": "center"},
                                    ),
                                ]
                            )
                        ]
                    ),
                ],
                id="card-block",
            )
        ),
    ]
)

tabla_prediction = dash_table.DataTable(
    id="datatable-prediction",
    # data=df.to_dict("records"),  # the contents of the table
    editable=False,  # allow editing of data inside all cells
    fixed_rows={"headers": True},
    filter_action="none",  # allow filtering of data by user ('native') or not ('none')
    sort_action="none",  # enables data to be sorted per-column by user or not ('none')
    sort_mode="multi",  # sort across 'multi' or 'single' columns
    sort_by=[{"column_id": "label", "direction": "desc"}],
    # column_selectable="multi",  # allow users to select 'multi' or 'single' columns
    # row_selectable="multi",  # allow users to select 'multi' or 'single' rows
    row_deletable=False,  # choose if user can delete a row (True) or not (False)
    selected_columns=[],  # ids of columns that user selects
    selected_rows=[],  # indices of rows that user selects
    page_action="native",  # all data is passed to the table up-front or not ('none')
    page_current=0,  # page number that user is on
    page_size=20,  # number of rows visible per page
    style_cell={  # ensure adequate header width when text is shorter than cell's text
        "minWidth": "180px",
        "width": "180px",
        "maxWidth": "180px",
        "font-family": "sans-serif",
        "textAlign": "center",
    },
    style_cell_conditional=[  # align text columns to left. By default they are aligned to right
        {"if": {"column_id": c}, "textAlign": "left"} for c in ["country", "iso_alpha3"]
    ],
    style_data={  # overflow cells' content into multiple lines
        "whiteSpace": "normal",
        "height": "auto",
    },
    style_as_list_view=True,
    style_header={
        "backgroundColor": "rgb(230, 230, 230)",
        "fontWeight": "bold",
    },
    style_table={
        "maxHeight": "50ex",
        "overflowY": "scroll",
        "width": "100%",
        "minWidth": "100%",
    },
)


layout = dbc.Container(
    [
        dcc.Interval(
            id="real-time-interval",
            disabled=False,  # if True, the counter will no longer update
            interval=30
            * 1000,  # increment the counter n_intervals every interval milliseconds
            # n_intervals=0,  # number of times the interval has passed
            # max_intervals=4,  # number of times the interval will be fired.
            # if -1, then the interval has no limit (the default)
            # and if 0 then the interval stops running.
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.H1("Real time prediction"),
                ),
            ]
        ),
        alert,
        cards_alerta,
        html.Br(),
        html.Div(
            style={
                "backgroundColor": "#494a4b",
                "padding": "6px 0px 6px 8px",
            },
            children=[
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Badge(
                                [
                                    html.H2(className="card-title", id="hora"),
                                    html.P("Last Updated", className="card-text"),
                                ],
                                color="dark",
                                style={"backgroundColor": "#494a4b"},
                                className="mr-1"
                            ),width=6
                        ),
                        dbc.Col(
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        "Open map",
                                        color="light",
                                        id="map-botton",
                                        className="mx-2",
                                    ),
                                    dbc.Button(
                                        "Open table",
                                        color="light",
                                        id="table-botton",
                                        className="mx-2",
                                    ),
                                ],
                                className="vertical-center",
                            ), width={'offset':3, 'size':3}
                        ),
                    ],
                    justify="between",
                ),
            ],
        ),
        dcc.Dropdown(
            options=[
                {"label": 'Comuneros - Primavera', "value": 1},
                {"label": 'Cerromatoso - Primavera', "value": 2},
                {"label": 'La Virginia - San Carlos', "value": 3},
            ],
            value=[1],
            multi=True,
            # labelStyle={"display": "inline-block"},
            id='checklist-linea'
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Collapse(
                        dcc.Graph(id="cluster-realtime-graph",config={"displayModeBar": False},),
                        id="map-collapse",
                        is_open=True,
                    )
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Collapse(tabla_prediction, id="table-collapse",is_open=True)
                ),
            ]
        ),
    ],
    fluid=True,
)


@app.callback(
    Output("map-collapse", "is_open"),
    Input("map-botton", "n_clicks"),
    State("map-collapse", "is_open"),
)
def toggle_left(n_left, is_open):
    if n_left:
        print('toogle map', not is_open)
        return not is_open
    return is_open


@app.callback(
    Output("table-collapse", "is_open"),
    Input("table-botton", "n_clicks"),
    State("table-collapse", "is_open"),
)
def toggle_left(n_left, is_open):
    if n_left:
        print('toogle table', not is_open)
        return not is_open
    return is_open