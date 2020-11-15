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

cache = Cache(
    app.server,
    config={
        # try 'filesystem' if you don't want to setup redis
        "CACHE_DIR": "cache",
        "CACHE_TYPE": "filesystem",
        # 'CACHE_REDIS_URL': os.environ.get('REDIS_URL', '')
    },
)

lineas_dict = {
    "comuneros": "Comuneros Primavera",
    "cerromatoso": "Cerromatoso Primavera",
    "virginia": "La Virginia San Carlos",
}
lineas_dict_numbers = {
    "comuneros": 1,
    "cerromatoso": 2,
    "virginia": 3,
}


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
        dcc.Store(id="memory-towers-model"),
        dcc.Store(id="memory-discharges-model"),
        dcc.Store(id="memory-outages-model"),
        dcc.Store(id="memory-features-model"),
        dcc.Store(id="memory-clusters-model"),
        dcc.Tabs(
            id="tabs-styled-with-props",
            value="tab-1",
            children=[
                dcc.Tab(
                    label="Clusters",
                    value="tab-1",
                    children=[
                        html.Hr(),
                        dbc.Row([dbc.Col(card) for card in cards]),
                        html.Label(
                            [
                                "Select power line:",
                                dcc.Dropdown(
                                    id="power_line_name_model",
                                    options=[
                                        {"label": lineas_dict[i], "value": i}
                                        for i in lineas_dict.keys()
                                    ],
                                    value="cerromatoso",
                                ),
                            ],
                            style={"width": "25%"},
                        ),
                        html.Label(
                            [
                                "Select outage:",
                                dcc.Loading(
                                    dcc.Dropdown(
                                        id="outage_dropdown_model", value="102"
                                    )
                                ),
                            ],
                            style={"width": "25%"},
                        ),
                    ],
                ),
                dcc.Tab(label="2", value="tab-2"),
            ],
        ),
        html.Div(
            id="tabs-content-props",
            children=html.Div(
                id="mini-layout",
                children=[
                    dcc.Loading(
                        dcc.Graph(id="fig-clusters", config={"displayModeBar": False})
                    )
                ],
            ),
        ),
        dash_table.DataTable(
            id="datatable-features",
            # data=df.to_dict("records"),  # the contents of the table
            editable=False,  # allow editing of data inside all cells
            fixed_rows={'headers': True},
            filter_action="none",  # allow filtering of data by user ('native') or not ('none')
            sort_action="native",  # enables data to be sorted per-column by user or not ('none')
            sort_mode="multi",  # sort across 'multi' or 'single' columns
            # column_selectable="multi",  # allow users to select 'multi' or 'single' columns
            # row_selectable="multi",  # allow users to select 'multi' or 'single' rows
            row_deletable=False,  # choose if user can delete a row (True) or not (False)
            selected_columns=[],  # ids of columns that user selects
            selected_rows=[],  # indices of rows that user selects
            page_action="native",  # all data is passed to the table up-front or not ('none')
            page_current=0,  # page number that user is on
            page_size=20,  # number of rows visible per page
            style_cell={  # ensure adequate header width when text is shorter than cell's text
                "minWidth": 95,
                "maxWidth": 95,
                "width": 95,
                "font-family": "sans-serif",
                "textAlign": "center",
            },
            style_cell_conditional=[  # align text columns to left. By default they are aligned to right
                {"if": {"column_id": c}, "textAlign": "left"}
                for c in ["country", "iso_alpha3"]
            ],
            style_data={  # overflow cells' content into multiple lines
                "whiteSpace": "normal",
                "height": "auto",
            },
            style_as_list_view=True,
            style_header={
                "backgroundColor": "rgb(230, 230, 230)",
                "fontWeight": "bold",
            },
            style_table={
                "maxHeight": "50ex",
                "overflowY": "scroll",
                "width": "100%",
                "minWidth": "100%",
            }
            # TODO Agregar en rojo si la prob es mayor al threhold
            # style_data_conditional=[
            #     {
            #         "if": {
            #             "filter_query": "{Humidity} > 19 && {Humidity} < 41",
            #             "column_id": "Humidity",
            #         },
            #         "color": "tomato",
            #         "fontWeight": "bold",
            #     },
            # ],
        ),
    ],
    className="ds4a-graphs",
)


@app.callback(
    Output("tabs-content-props", "children"),
    [Input("tabs-styled-with-props", "value")],
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


@app.callback(
    [Output("fig-clusters", "figure"),Output('datatable-features', 'data'),Output('datatable-features', 'columns')],
    [
        Input("power_line_name_model", "value"),
        Input("outage_dropdown_model", "value"),
        Input("memory-towers-model", "data"),
        Input("memory-clusters-model", "data"),
        Input("memory-features-model", "data"),
    ],
)
# @cache.memoize(timeout=1000)
def updating(power_line_name_model, outage_indicatoes, data_towers, data_clusters, data_features):
    towers = pd.DataFrame.from_dict(data_towers)
    df_clusters = pd.DataFrame.from_dict(data_clusters)
    df_features = pd.DataFrame.from_dict(data_features)
    # outages = pd.DataFrame.from_dict(data_outages)
    # discharges = pd.DataFrame.from_dict(data_discharges)
    print("Hola")
    print("clustes", df_clusters.cluster.head(2))
    cols = df_clusters.columns.drop(['date','date_outage'])
    df_clusters[cols] = df_clusters[cols].apply(pd.to_numeric)
    df_clusters.cluster = df_clusters.cluster.astype("int64")
    df_clusters.cluster = pd.Categorical(df_clusters.cluster)
    # map_fig =  go.Figure()
    map_fig = px.scatter_mapbox(
            df_clusters,
            lat="latitude",
            lon="longitude",
            color="cluster",
            hover_data=["time_delta", "date"])
        
    map_fig.add_trace(
        go.Scattermapbox(
            lat=towers.latitude,
            lon=towers.longitude,
            mode="markers",  # markers+lines
            marker=go.scattermapbox.Marker(size=7, color="black", opacity=0.7),
            name="Towers",
            hovertemplate="longitude: %{lon:.2f}<br>" + "latitude: %{lat:.2f}<br>",
        )
    )
    df_clusters.lat_failure = pd.to_numeric(df_clusters.lat_failure)
    df_clusters.lon_failure = pd.to_numeric(df_clusters.lon_failure)
    df_failure = df_clusters.drop_duplicates(subset=["lon_failure", "lat_failure"])
    map_fig.add_trace(
        go.Scattermapbox(
            lat=df_failure.lat_failure,
            lon=df_failure.lon_failure,
            mode="markers",  # markers+lines
            marker=dict(size=20, symbol=["hardware"], color="red"),
            name="Falla",
            hovertemplate="longitude: %{lon:.2f}<br>" + "latitude: %{lat:.2f}<br>",
        )
    )

    # map_fig.add_trace(
    #     go.Scattermapbox(
    #         lat=df_clusters.latitude,
    #         lon=df_clusters.longitude,
    #         mode="markers",  # markers+lines
    #         marker=go.scattermapbox.Marker(
    #             size=7, opacity=0.7, color=df_clusters.cluster,
    #         ),
    #         name="Clusters",
    #         showlegend=True,
    #         # showscale=False,
    #         hovertemplate="longitude: %{lon:.2f}<br>" + "latitude: %{lat:.2f}<br>",
    #     )
    # )

    lon_x, lon_y, gdf_buffer = buf.buffer_line(10, towers_buffer=towers)
    centro = gdf_buffer.centroid
    x = centro.x.iloc[0]
    y = centro.y.iloc[0]
    map_fig.update_layout(
        margin={"t": 0.2, "l": 0, "b": 10},
        autosize=True,
        height=500,
        hovermode="closest",
        mapbox=dict(
            accesstoken=mapbox_token,
            style=mapstyle,
            center=dict(lat=y, lon=x),
            zoom=9,
        ),
        #     legend=dict(
        #     x=0,
        #     y=1,
        #     traceorder="reversed",
        #     title_font_family="Times New Roman",
        #     font=dict(
        #         family="Courier",
        #         size=12,
        #         color="black"
        #     ),
        #     bgcolor="LightSteelBlue",
        #     bordercolor="Black",
        #     borderwidth=2
        # )
    )
    map_fig["layout"]["uirevision"] = "no reset of zoom"
    formato = Format(
                scheme=Scheme.fixed, 
                precision=2,
                group=Group.yes,
                groups=3,
                group_delimiter='.',
                decimal_delimiter=',')
    
    formato_int = Format(
                scheme=Scheme.fixed, 
                precision=0,
                group=Group.yes,
                groups=3,
                group_delimiter='.',
                decimal_delimiter=',')
    
    df_features.index = pd.to_numeric(df_features.index)
    df_features.index.name = 'Cluster'
    df_table = df_features.join(df_clusters.drop_duplicates('cluster').set_index('cluster')[['date_outage']]).dropna()
    df_table.reset_index(inplace=True)
    df_table.index = df_table.index.astype('int')
    cols = df_table.columns.drop('date_outage')
    df_table[cols] = df_table[cols].apply(pd.to_numeric)
    
    df_numeric = df_table.select_dtypes(exclude=['object'])
    cols = [{"name": i, "id": i, 'type': 'numeric',
            'format':formato_int if i in ['Cluster','label','line'] else formato} for i in df_numeric.columns]
    return map_fig, df_numeric.to_dict('records'), cols

