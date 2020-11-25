import lib.st_dbscan_model as st_dbscan_model
import lib.features as features
import lib.svm_predictor as svm_predictor
import data.data_import_DB_L2 as di_db
import pandas as pd
from dash.exceptions import PreventUpdate
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
from pathlib import Path

# Recall app
import data.data_import_DB_L2

from app import app
from dash.dependencies import ClientsideFunction, Input, Output, State
import dash_table
import lib.buffer as buf

from flask_caching import Cache

from lib.stats import mapbox_token
from lib.stats import mapstyle


# Buffering

import lib.buffer as buffer

# ******* change ************************
df_towers = pd.read_csv(
    Path(r"./data/towers1.csv"), header=0, delimiter=",", index_col=0
)
# ****************************************

# ST-DBSCAN
discharges_df, current_datetime = di_db.discharges_last_5hours()

x_buffer, y_buffer, buffer_dist = buffer.buffer_line(
    distance=30, towers_buffer=df_towers
)
discharges_gdf = features.convertir_gdf(discharges_df)
discharges_df = discharges_gdf.loc[
    discharges_gdf.within(buffer_dist.geometry.iloc[0])
].copy()

# model parameters
eps1_km = 10  # spatial distance of 10 km
eps2 = 10  # temporal distance of 10 min
min_samples = 5  # min number of dicharges in cluster nuclei
km_per_radian = 6371.0088
eps1 = eps1_km / km_per_radian

data_array = st_dbscan_model.data_preparation(
    discharges_df=discharges_df, current_datetime=current_datetime
)
labels = st_dbscan_model.st_dbscan(
    eps1=eps1, eps2=eps2, min_samples=min_samples, data_array=data_array
)

# Contiene la info de las descargar
# TODO cruzarlo
discharges_by_cluster_df = st_dbscan_model.discharges_by_cluster(
    data_array=data_array, labels=labels, discharges_df=discharges_df
)


raw_features_df = features.extract_features(
    df_discharges=discharges_by_cluster_df, df_towers=df_towers
)
clean_features_df = features.clean_features(raw_features_df=raw_features_df)

# SVM PREDICTION
path = r"./predictor/"
pkl_filename = "SVM_model.pkl"

prediction = svm_predictor.predict_outage(
    path=path, pkl_filename=pkl_filename, clean_features_df=clean_features_df
)
prediction_df = svm_predictor.create_prediction_df(
    clean_features_df=clean_features_df, prediction=prediction, threshold=0.3
)

#! Con este. El mas importante
# TODO Tabla de predicciones  y features
filter_prediction_df = svm_predictor.filter_predictions(prediction_df=prediction_df)
print("MAXIMO", filter_prediction_df.prediction.max())

clusters_id_final = filter_prediction_df.index
discharges_by_cluster_df_temp = discharges_by_cluster_df[
    discharges_by_cluster_df.cluster.isin(clusters_id_final)
]


def get_realtime_figure(
    df_clusters=discharges_by_cluster_df_temp,
    towers=df_towers,
    df_features=filter_prediction_df,
):
    df_clusters.cluster = pd.Categorical(df_clusters.cluster)
    map_fig = px.scatter_mapbox(
        df_clusters,
        lat="latitude",
        lon="longitude",
        color="cluster",
        hover_data=["time_delta", "date"],
    )

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
            zoom=8,
        ),
    )
    map_fig["layout"]["uirevision"] = "no reset of zoom"
    return map_fig


# print('La figura',get_realtime_figure()
figure = get_realtime_figure()


@app.callback(
    [
        Output("cluster-realtime-graph", "figure"),
        Output("hora", "children"),
        Output("card-prob-1", "children"),
        Output("datatable-prediction", "data"),
        Output("datatable-prediction", "columns"),
        Output("datatable-prediction", "style_data_conditional"),
    ],
    [
        Input("real-time-interval", "n_intervals"),
    ],
)
def update_graph(num):
    # print("""update every 3 seconds""")
    if num == 0:
        raise PreventUpdate
    else:
        df_table = filter_prediction_df.copy()
        formato = Format(
            scheme=Scheme.fixed,
            precision=2,
            group=Group.yes,
            groups=3,
            group_delimiter=".",
            decimal_delimiter=",",
        )

        formato_int = Format(
            scheme=Scheme.fixed,
            precision=0,
            group=Group.yes,
            groups=3,
            group_delimiter=".",
            decimal_delimiter=",",
        )
        df_table.index.name = "Cluster"
        df_table.reset_index(inplace=True)
        # cols = df_table.columns.drop("date_outage")
        cols = df_table.columns
        df_table[cols] = df_table[cols].apply(pd.to_numeric)
        df_numeric = df_table.select_dtypes(exclude=["object"])
        df_numeric.sort_values("Cluster", ascending=True, inplace=True)
        df_numeric.columns = df_numeric.columns.map(lambda x: x.replace("_", " "))
        cols = [
            {
                "name": i,
                "id": i,
                "type": "numeric",
                "format": formato_int if i in ["Cluster", "label", "line"] else formato,
            }
            for i in df_numeric.columns
        ]
        style_data_conditional = [
            {
                "if": {"filter_query": "{label} = 1"},
                "backgroundColor": "#FF4136",
                "color": "white",
                "fontWeight": "bold",
            },
        ]
        return (
            figure,
            dt.now().strftime("%H:%M:%S"),
            "{:.1f}%".format(filter_prediction_df.prediction.max() * 100),
            df_numeric.to_dict("records"),
            cols,
            style_data_conditional,
        )
