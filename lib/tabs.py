import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px


from datetime import datetime as dt
import json
import numpy as np
import pandas as pd
import os

# Recall app
from app import app


tabs = html.Div([
    dcc.Tabs(id="tabs-styled-with-props", value='tab-1', children=[
        dcc.Tab(label='Histograma', value='tab-1'),
        dcc.Tab(label='2', value='tab-2'),
    ]),
    html.Div(id='tabs-content-props',children=[dcc.Graph(id='histo')])], className="ds4a-graphs")

@app.callback(Output('histo', 'figure'),
              [Input('tabs-styled-with-props', 'value')])
def render_content(tab):
    print(tab)
    if tab == 'tab-1':
        df2 = px.data.iris()
        figurita = px.scatter(df2, x="sepal_width", y="sepal_length", color="species", marginal_y="violin",
                marginal_x="box", trendline="ols", template="simple_white")
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