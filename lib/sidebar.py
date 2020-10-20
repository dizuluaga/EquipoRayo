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

DS4A_Img = html.Div(
    children=[html.Img(src=app.get_asset_url("ds4a-img.svg"), id="ds4a-image",)],
)

ISA_Img = html.Div(
    children=[html.Img(src=app.get_asset_url("ISA_logo.png"), id="logo-image",style={"width": "100%"})],

)

#############################################################################
# State Dropdown
#############################################################################
# DATA_DIR = "data"
# states_path = os.path.join(DATA_DIR, "states.json")
# with open(states_path) as f:
#     states = json.loads(f.read())
#  outages = pd.read_csv('./data/outages.csv', header=0, delimiter=',', index_col=0,
#                      names=['date', 'year', 'time', 'cause', 'outages_number', 'r_inf', 'r_sup'], parse_dates=['date'])
available_indicators = stats.outages.index
dropdown = dcc.Dropdown(
    id="outage_dropdown",
    options=[{"label": stats.outages.loc[i,'date'].strftime('%Y-%m-%d'), "value": i} for i in available_indicators],
    value='57',
    multi=False,
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
sidebar = html.Div(
    [
        DS4A_Img,  # Add the DS4A_Img located in the assets folder
        html.Hr(),  # Add an horizontal line
        ####################################################
        # Place the rest of Layout here
        ####################################################
        html.H4("Team 4"),
        html.Hr(),
        html.H5("Select dates"),
        date_picker,
        html.Hr(),
        html.H5("Select outage"),
        dropdown,
        html.Hr(),
        ISA_Img
    ],
    className="ds4a-sidebar",
)
