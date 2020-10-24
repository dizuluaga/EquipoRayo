# Libraries
import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import dash_bootstrap_components as dbc
from datetime import timedelta

# Recall app
from app import app

###########################################################
#
#           APP LAYOUT:
#
###########################################################

# LOAD THE DIFFERENT FILES
from lib import title, sidebar, stats, tabs

# PLACE THE COMPONENTS IN THE LAYOUT
app.layout = html.Div(
    [title.title, sidebar.sidebar, stats.stats, tabs.tabs],
    className = "ds4a-app",  # You can also add your own css files by locating them into the assets folder
)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port="8050", debug=True)
