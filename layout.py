# Libraries
from lib import about_us
import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import dash_table

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import dash_bootstrap_components as dbc
from datetime import timedelta
import sys

# Recall app
from app import app

###########################################################
#           APP LAYOUT:
###########################################################

# LOAD THE DIFFERENT FILES
from lib import sidebar, stats, tabs, about_us

import data.data_import_DB

# PLACE THE COMPONENTS IN THE LAYOUT
content = html.Div(id="page-content", children=[])

app.layout = html.Div(
    [
        dcc.ConfirmDialog(
            id="confirm",
            message="No outages were found! Please select another date.",
        ),
        dcc.Store(id="memory-towers"),
        dcc.Store(id="memory-discharges"),
        dcc.Store(id="memory-outages"),
        dcc.Location(id="url", refresh=False),
        sidebar.sidebar,
        content,
    ],
    className="ds4a-app",  # You can also add your own css files by locating them into the assets folder
)

# poner los nombres de los href de sidebar.py
pathnames_dict = {
    "/page-1": "/exploratory",
    "/page-2": "/model",
    "/page-3": "/about-us",
}

# this callback uses the current pathname to set the active state of the
# corresponding nav link to true, allowing users to tell see page they are on
@app.callback(
    [Output(f"page-{i}-link", "active") for i in range(1, 4)],
    [Input("url", "pathname")],
)
def toggle_active_links(pathname):
    if pathname == "/":
        # Treat page 1 as the homepage / index
        return False, True, False
    else:
        return [pathname == pathnames_dict.get(f"/page-{i}") for i in range(1, 4)]


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    if pathname == pathnames_dict["/page-1"]:
        return stats.layout
    elif pathname == pathnames_dict["/page-2"]:
        return tabs.layout
    elif pathname == pathnames_dict["/page-3"]:
        return about_us.layout
    elif pathname == "/":
        return html.Div(html.H1("Isa Project"), className="ds4a-body")
        # TODO
    else:
        return html.Div(
            [
                dbc.Jumbotron(
                    [
                        html.H1("404: Not found", className="text-danger"),
                        html.Hr(),
                        html.P(f"The pathname {pathname} was not recognised..."),
                    ]
                )
            ],
            className="ds4a-graphs",
        )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        app.run_server(host="0.0.0.0", debug=False) if (
            sys.argv[1] == "online"
        ) else None
    else:
        app.run_server(host="0.0.0.0", debug=True)
