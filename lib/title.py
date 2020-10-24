# Basics Requirements
import pathlib
import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html

# Dash Bootstrap Components
import dash_bootstrap_components as dbc

# Recall app
from app import app

title = html.Div(
    className="ds4a-title",
    children=[
        dbc.Row(
            dbc.Col(html.H1("Comuneros-Primavera Power Line"),
                    width={
                        "size": 7,
                        "offset": 3,
                        'color': '#F8F9F9'
                    }))
    ],
    id="title",
)