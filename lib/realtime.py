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
        html.H4("Well done!", className="alert-heading"),
        html.P(
            "This is a success alert with loads of extra text in it. So much "
            "that you can see how spacing within an alert works with this "
            "kind of content."
        ),
        html.Hr(),
        html.P(
            "Let's put some more text down here, but remove the bottom margin",
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
                html.H2(id = 'card-probability', className="card-title"),
                html.P("Probability of outage", className="card-text"),
            ],id='card-block',
            body=True,
            color="danger",
        )
    ),
    html.Br(),
    # dbc.Card(
    #     [
    #         html.H2(f"{0.75*100:.1f}%", className="card-title"),
    #         html.P("Model Test Accuracy", className="card-text"),
    #     ],
    #     body=True,
    #     color="dark",
    #     inverse=True,
    # ),
    dbc.Row(
        dbc.Card(
            [
                html.H2(className="card-title", id='hora'),
                html.P("Time H-M-S", className="card-text"),
            ],
            body=True,
            color="primary",
            inverse=True,
        ),
    ),
]


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
                dbc.Col(html.Div(cards_alerta), md=2),
                dbc.Col(
                    dcc.Input(
                        id="camilo",
                        type="number",
                        placeholder="input with range",
                        min=10,
                        max=100,
                        step=3,
                    )
                ),
            ],
            align="center",
        ),
    ],
    fluid=True,
)

