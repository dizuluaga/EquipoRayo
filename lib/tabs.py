import json
import os
from datetime import datetime as dt

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
# Recall app
from app import app
from dash.dependencies import ClientsideFunction, Input, Output, State

tabs = html.Div(
    [
        dcc.Tabs(
            id="tabs-styled-with-props",
            value='tab-1',
            children=[
                dcc.Tab(
                    label='Histograma',
                    value='tab-1',
                    children=[
                        #RadioItems por una sola opcion, dcc.Checklist para varios.
                        dcc.RadioItems(options=[
                            {
                                'label': 'Density',
                                'value': 'NYC'
                            },
                            {
                                'label': 'Accumulated',
                                'value': 'MTL'
                            },
                        ],
                                       value='NYC',
                                       className='my_box_container',
                                       inputClassName='my_box_input',
                                       labelClassName='my_box_label')
                    ]),
                dcc.Tab(label='2', value='tab-2'),
            ]),
        html.Div(id='tabs-content-props', children=[dcc.Graph(id='histo')])
    ],
    className="ds4a-graphs")


@app.callback(Output('histo', 'figure'),
              [Input('tabs-styled-with-props', 'value')])
def render_content(tab):
    print(tab)
    if tab == 'tab-1':
        df2 = px.data.iris()
        figurita = px.scatter(df2,
                              x="sepal_width",
                              y="sepal_length",
                              color="species",
                              marginal_y="violin",
                              marginal_x="box",
                              trendline="ols",
                              template="simple_white")
        return figurita
    elif tab == 'tab-2':
        fig = px.scatter(x=[0, 1, 2, 3, 4], y=[0, 1, 4, 9, 16])
        return fig

    #     return html.Div([
    #         html.H3('Tab content 1')
    # #     ])
    # elif tab == 'tab-2':
    #     return html.Div([
    #         html.H3('Tab content 2')
    #     ])
