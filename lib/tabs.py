import json
import os
from datetime import datetime as dt

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
from app import app
from dash.dependencies import ClientsideFunction, Input, Output, State
import dash_table

cards = [
    dbc.Card(
        [
            html.H2(f"{0.85*100:.1f}%", className="card-title"),
            html.P("Model Training Accuracy", className="card-text"),
        ],
        body=True,
        color="light",
    ),
    dbc.Card(
        [
            html.H2(f"{0.75*100:.1f}%", className="card-title"),
            html.P("Model Test Accuracy", className="card-text"),
        ],
        body=True,
        color="dark",
        inverse=True,
    ),
    dbc.Card(
        [
            html.H2("50 / 60", className="card-title"),
            html.P("Train / Test Split", className="card-text"),
        ],
        body=True,
        color="primary",
        inverse=True,
    ),
]

df = px.data.iris()

layout = html.Div(
    [
        dbc.Row([dbc.Col(card) for card in cards]),
        html.Hr(),
        dcc.Tabs(
            id="tabs-styled-with-props",
            value="tab-1",
            children=[
                dcc.Tab(
                    label="Clusters",
                    value="tab-1",
                    children=[
                        # RadioItems por una sola opcion, dcc.Checklist para varios.
                        dcc.RadioItems(
                            options=[
                                {"label": "Historical", "value": "NYC"},
                                {"label": "Real-Time", "value": "MTL"},
                            ],
                            value="NYC",
                            className="my_box_container",
                            inputClassName="my_box_input",
                            labelClassName="my_box_label",
                        )
                    ],
                ),
                dcc.Tab(label="2", value="tab-2"),
            ],
        ),
        html.Div(id="tabs-content-props"),
        dash_table.DataTable(
            id="datatable-interactivity",
            columns=[
                {
                    "name": i,
                    "id": i,
                    "deletable": True,
                    "selectable": True,
                    "hideable": True,
                }
                if i == "iso_alpha3" or i == "year" or i == "id"
                else {"name": i, "id": i, "deletable": True, "selectable": True}
                for i in df.columns
            ],
            data=df.to_dict("records"),  # the contents of the table
            editable=True,  # allow editing of data inside all cells
            filter_action="native",  # allow filtering of data by user ('native') or not ('none')
            sort_action="native",  # enables data to be sorted per-column by user or not ('none')
            sort_mode="single",  # sort across 'multi' or 'single' columns
            column_selectable="multi",  # allow users to select 'multi' or 'single' columns
            row_selectable="multi",  # allow users to select 'multi' or 'single' rows
            row_deletable=True,  # choose if user can delete a row (True) or not (False)
            selected_columns=[],  # ids of columns that user selects
            selected_rows=[],  # indices of rows that user selects
            page_action="native",  # all data is passed to the table up-front or not ('none')
            page_current=0,  # page number that user is on
            page_size=6,  # number of rows visible per page
            style_cell={  # ensure adequate header width when text is shorter than cell's text
                "minWidth": 95,
                "maxWidth": 95,
                "width": 95,
            },
            style_cell_conditional=[  # align text columns to left. By default they are aligned to right
                {"if": {"column_id": c}, "textAlign": "left"}
                for c in ["country", "iso_alpha3"]
            ],
            style_data={  # overflow cells' content into multiple lines
                "whiteSpace": "normal",
                "height": "auto",
            },
        ),
    ],
    className="ds4a-graphs",
)


df2 = px.data.iris()
fig = px.scatter(
    df2,
    x="sepal_width",
    y="sepal_length",
    color="species",
    marginal_y="violin",
    marginal_x="box",
    trendline="ols",
    template="simple_white",
)
mini_layout = html.Div(id="tabs-content-props", children=[dcc.Graph(figure=fig)])


@app.callback(
    Output("tabs-content-props", "children"), [Input("tabs-styled-with-props", "value")]
)
def render_content(tab):
    print(tab)
    if tab == "tab-1":
        global mini_layout
        layout = mini_layout
        return layout
    elif tab == "tab-2":
        fig = px.scatter(x=[0, 1, 2, 3, 4], y=[0, 1, 4, 9, 16])
        mini_layout2 = html.Div(id="tabs-cont", children=[dcc.Graph(figure=fig)])
        return mini_layout2

    #     return html.Div([
    #         html.H3('Tab content 1')
    # #     ])
    # elif tab == 'tab-2':
    #     return html.Div([
    #         html.H3('Tab content 2')
    #     ])


# -------------------------------------------------------------------------------------
# Highlight selected column
@app.callback(
    Output("datatable-interactivity", "style_data_conditional"),
    [Input("datatable-interactivity", "selected_columns")],
)
def update_styles(selected_columns):
    return [
        {"if": {"column_id": i}, "background_color": "#D2F3FF"}
        for i in selected_columns
    ]


# -------------------------------------------------------------------------------------
