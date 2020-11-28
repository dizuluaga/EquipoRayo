# Basics Requirements
import pathlib
import os
import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html


# Dash Bootstrap Components
import dash_bootstrap_components as dbc

# Data
import json
from datetime import datetime as dt
from lib import stats

# Recall app
from app import app


####################################################################################
# Add the DS4A_Img
####################################################################################

simte_Img = html.Div(
    children=[
        html.Img(
            src=app.get_asset_url("logo-simte.png"),
            id="simt-image",
            style={"width": "85%"},
        )
    ], style={'textAlign': 'center'}
)


DS4A_Img = html.Div(
    children=[
        html.Img(
            src=app.get_asset_url("ds4a-img.svg"),
            id="ds4a-image",
        )
    ],
)

ISA_Img = html.Div(
    children=[
        html.Img(
            src=app.get_asset_url("ISA_logoblanco.png"),
            id="logo-image",
            style={"width": "85%"},
        )
    ], style={'textAlign': 'center'}
)

MINTIC_Img = html.Div(
    children=[
        html.Img(
            src=app.get_asset_url("logo-mintic.png"),
            id="logo-mintic",
            style={"width": "100%"},
        )
    ],style={'textAlign': 'center'}
)


##############################################################################
# Date Picker
##############################################################################

date_picker = dcc.DatePickerRange(
    id="date_picker",
    min_date_allowed=dt(2014, 1, 2),
    max_date_allowed=dt(2017, 12, 31),
    start_date=dt(2016, 1, 1).date(),
    end_date=dt(2017, 1, 1).date(),
)


#############################################################################
# Sidebar Layout
#############################################################################
sidebar = html.Div([
    # [
    #     DS4A_Img,  # Add the DS4A_Img located in the assets folder
    #     html.H4("Team 4",style={'textAlign': 'center'}),
        # html.Hr(),  # Add an horizontal line
        ####################################################
        # Place the rest of Layout here
        ####################################################
        simte_Img,
        html.Hr(),
        # dcc.Link(html.Button('back'), href='www.google.com'),
        dbc.Nav(
            [
                dbc.NavLink(
                        html.Span(
                            [html.I(className="fas fa-cloud", style={"margin-right": "0.5rem"}),
                             "Exploratory Analysis", 
                            ],
                    ),
                    href="/exploratory",
                    id="page-1-link",
                    className='text-dark',
                ),
                dbc.NavLink(
                    html.Span(
                            [html.I(className="fa fa-tasks", style={"margin-right": "0.5rem"}),
                             "Outage prediction", 
                            ],
                    ),
                    href="/model",
                    id="page-2-link",
                    className="text-dark",
                ),
                dbc.NavLink(
                   html.Span(
                            [html.I(className="fa fa-users", style={"margin-right": "15px"}),
                             "About us", 
                            ],),
                    href="/about-us",
                    id="page-3-link",
                    className="text-dark",
                ),
            ],
            vertical=True,
            pills=True
        ),
        html.Hr(),
        ISA_Img,
        html.Hr(),
        DS4A_Img,
        MINTIC_Img,
    ],
    className="ds4a-sidebar",
)
