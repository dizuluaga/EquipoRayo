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
)


cards_alerta = [dbc.Row(
    dbc.Card(
        [
            html.H2(f"{0.85*100:.1f}%", className="card-title"),
            html.P("Model Training Accuracy", className="card-text"),
        ],
        body=True,
        color="light",)
    ),
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
            html.H2("50 / 60", className="card-title"),
            html.P("Train / Test Split", className="card-text"),
        ],
        body=True,
        color="primary",
        inverse=True,
    ),)
]


layout = dbc.Container(
    [
        dcc.Interval(id="interval-component"),
        html.H1("Real time prediction"),
        html.Hr(),
        alert,
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="cluster-graph"), md=8),
                dbc.Col(
                    html.Div(cards_alerta), md=4),
            ],
            align="center",
        ),
    ],
    fluid=True,
)