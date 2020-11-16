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
from real_time_app import discharges_by_cluster_df

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
            "It is likely that in the next 5 minutes there will be a failure in the Comuneros-Primavera power line."
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
    color="danger",
)


cards_alerta = [
    dbc.Row(
        dbc.Card(
            [
                html.H2(id="card-probability", className="card-title"),
                html.P("Probability of outage", className="card-text"),
            ],
            id="card-block",
            body=True,
            color="danger",
        )
    ),
    html.Br(),
    dbc.Row(
        dbc.Card(
            [
                html.H2(className="card-title", id="hora"),
                html.P("Time HH:MM:SS", className="card-text"),
            ],
            body=True,
            color="dark",
            inverse=True,
        ),
    ),
]


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
            interval=1
            * 1000,  # increment the counter n_intervals every interval milliseconds
            # n_intervals=0,  # number of times the interval has passed
            # max_intervals=4,  # number of times the interval will be fired.
            # if -1, then the interval has no limit (the default)
            # and if 0 then the interval stops running.
        ),
        html.H1("Real time prediction"),
        alert,
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="cluster-realtime-graph"), md=8),
                dbc.Col(html.Div(cards_alerta), md=4),
            ],
            align="center",
        ),
        tabla_prediction,
    ],
    fluid=True,
)
