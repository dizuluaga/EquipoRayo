import lib.st_dbscan_model as st_dbscan_model
import lib.features as features
import lib.svm_predictor as svm_predictor
import data.data_import_DB_L2 as di_db_2
import data.data_import_DB as di_db
import pandas as pd
from dash.exceptions import PreventUpdate
import json
from lib import buffer
import os
from datetime import datetime as dt
from datetime import timedelta
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

import warnings

warnings.filterwarnings("ignore")

# Recall app
import data.data_import_DB_L2

from app import app
from dash.dependencies import ClientsideFunction, Input, Output, State
import dash_table
import lib.buffer as buf

from flask_caching import Cache

from lib.stats import mapbox_token
from lib.stats import mapstyle
import lib.buffer as buffer

# time libraries
from timeit import default_timer as timer

start_abs = timer()


def movecol(df, cols_to_move=[], ref_col="", place="After"):
    """[summary]

    Args:
        df ([type]): [description]
        cols_to_move (list, optional): [description]. Defaults to [].
        ref_col (str, optional): [description]. Defaults to ''.
        place (str, optional): [description]. Defaults to 'After'.
    """
    cols = df.columns.tolist()
    if place == "After":
        seg1 = cols[: list(cols).index(ref_col) + 1]
        seg2 = cols_to_move
    if place == "Before":
        seg1 = cols[: list(cols).index(ref_col)]
        seg2 = cols_to_move + [ref_col]

    seg1 = [i for i in seg1 if i not in seg2]
    seg3 = [i for i in cols if i not in seg1 + seg2]

    return df[seg1 + seg2 + seg3]


## INITIALIZATION

towers_1 = di_db.towers_1
towers_2 = di_db.towers_2
towers_3 = di_db.towers_3

# initialize ST-DBSCAN parameters
eps1_km = 10  # spatial distance of 10 km
eps2 = 10  # temporal distance of 10 min
min_samples = 5  # min number of dicharges in cluster nuclei
km_per_radian = 6371.0088
eps1 = eps1_km / km_per_radian

# define predictor path
predictor_path = r"./predictor/"
pkl_filename = "SVM_model.pkl"

towers_dict = {1: di_db.towers_1, 2: di_db.towers_2, 3: di_db.towers_3}
discharges_by_cluster_dict = {}
filter_prediction_dict = {}
mapping = {1: {}, 2: {}, 3: {}}


def api():
    total_clusters = 0
    for line in range(1, 4):

        ## DATA COLLECTION AND FILTERING
        start = timer()
        # get discharges and filter by time (last 24 hours)
        discharges_df, current_datetime = di_db_2.discharges_last_24hours(
            table_id=line
        )  # CHANGE FUNC

        if not discharges_df.empty:
            # get towers from DB
            towers_df = towers_dict[line]

            # filter discharges within buffer area
            x_buffer, y_buffer, buffer_dist = buffer.buffer_line(
                distance=30, towers_buffer=towers_df
            )
            discharges_gdf = features.convertir_gdf(discharges_df)
            discharges_df = discharges_gdf.loc[
                discharges_gdf.within(buffer_dist.geometry.iloc[0])
            ]

            end = timer()
            print("data collection line {}: {}".format(line, end - start))

            if not discharges_df.empty:

                ## CLUSTERING
                start = timer()
                # prepare discharges to be enter to ST-DBSCAN algorithm
                data_array = st_dbscan_model.data_preparation(
                    discharges_df=discharges_df, current_datetime=current_datetime
                )
                # ST-DBSCAN algorithm
                labels = st_dbscan_model.st_dbscan(
                    eps1=eps1, eps2=eps2, min_samples=min_samples, data_array=data_array
                )

                # construct dataframe using ST-DBSCAN output
                discharges_by_cluster_df = st_dbscan_model.discharges_by_cluster(
                    data_array=data_array, labels=labels, discharges_df=discharges_df
                )

                end = timer()
                print("clustering line {}: {}".format(line, end - start))

                ## FEATURIZATION
                start = timer()
                # construct features
                clean_features_df = features.extract_features(
                    df_discharges=discharges_by_cluster_df, df_towers=towers_df
                )

                # clean noise and poor clusters of features dataframe
                # clean_features_df = features.clean_features(raw_features_df=raw_features_df)

                end = timer()
                print("featurization line {}: {}".format(line, end - start))

                ## PREDICTION
                start = timer()
                # perform SVM prediction
                prediction = svm_predictor.predict_outage(
                    path=predictor_path,
                    pkl_filename=pkl_filename,
                    clean_features_df=clean_features_df,
                )

                # create and filter dataframe from prediction output
                filter_prediction_df = svm_predictor.create_prediction_df(
                    clean_features_df=clean_features_df,
                    prediction=prediction,
                    threshold=0.3,
                )
                filter_prediction_dict[line] = filter_prediction_df
                end = timer()
                print("prediction line {}: {}".format(line, end - start))

                # get discharges belonging to filtered clusters
                clusters_prediction_index = filter_prediction_dict[line].index
                discharges_by_cluster_dict[line] = discharges_by_cluster_df[
                    discharges_by_cluster_df.cluster.isin(clusters_prediction_index)
                ]

                for i, cluster_ori in enumerate(clusters_prediction_index):
                    mapping[line][cluster_ori] = i + 1 + total_clusters
                cluster_count = len(clusters_prediction_index)
                total_clusters += cluster_count
                discharges_by_cluster_dict[line][
                    "cluster"
                ] = discharges_by_cluster_df.cluster.map(mapping[line])
                filter_prediction_dict[line][
                    "cluster"
                ] = filter_prediction_df.index.map(mapping[line])

    return discharges_by_cluster_dict, filter_prediction_dict


end_abs = timer()
print("Total: {}".format(end_abs - start_abs))

discharges_by_cluster_dict, filter_prediction_dict = api()
# def get_realtime_figure(
#     df_clusters=discharges_by_cluster_df_temp,
#     towers=df_towers,
#     df_features=filter_prediction_df,
# ):
def get_realtime_figure(lista_lineas=[1, 2, 3]):
    """[summary]

    Args:
        lista_lineas (list, optional): [description]. Defaults to [1,2,3].

    Returns:
        [type]: [description]
    """
    map_fig = go.Figure()
    for linea in lista_lineas:
        df_clusters = discharges_by_cluster_dict[linea]
        df_clusters.cluster = pd.Categorical(df_clusters.cluster)

        map_fig.add_trace(
            go.Scattermapbox(
                lat=df_clusters["latitude"],
                lon=df_clusters["longitude"],
                marker=go.scattermapbox.Marker(
                    size=7, color=df_clusters["cluster"], opacity=0.7
                ),
                legendgroup=str(linea),
                name="Linea_" + str(linea),
                customdata=pd.concat(
                    [
                        df_clusters.cluster,
                        df_clusters.date.dt.strftime("%H:%M:%S"),
                        df_clusters.time_delta,
                        df_clusters.magnitude,
                        df_clusters.polarity,
                        df_clusters.current,
                    ],
                    axis=1,
                ).values,
                hovertemplate="<b>Cluster: %{customdata[0]}</b><br><b>Time: %{customdata[1]}</b><br><br>Time delta (min): %{customdata[2]:.1f}</b><br>Magnitude: %{customdata[3]:.1f}</b><br>Polarity: %{customdata[4]:.0f}",
            )
        )

        # Grafico las torres
        map_fig.add_trace(
            go.Scattermapbox(
                lat=(towers_dict[linea]).latitude,
                lon=(towers_dict[linea]).longitude,
                mode="markers",  # markers+lines
                marker=go.scattermapbox.Marker(size=7, color="black", opacity=0.7),
                name="Towers",
                showlegend=False,
                hovertemplate="longitude: %{lon:.2f}<br>" + "latitude: %{lat:.2f}<br>",
                legendgroup=str(linea),
            )
        )
    map_fig.update_layout(
        margin={"t": 0.2, "l": 0, "b": 10},
        autosize=True,
        height=600,
        hovermode="closest",
        mapbox=dict(
            accesstoken=mapbox_token,
            style=mapstyle,
            center=dict(lat=6.58, lon=-74.6),
            zoom=8,
        ),
    )
    # print("Mapg figureeee", map_fig)
    map_fig["layout"]["uirevision"] = "no reset of zoom"
    return map_fig


def get_table(lista_lineas=[1, 2, 3]):
    tables = []
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
    for linea in lista_lineas:
        filter_prediction_df = filter_prediction_dict[linea]
        # print("ensayooo", filter_prediction_df.head())
        df_table = filter_prediction_df.copy()

        df_table.reset_index(drop=True, inplace=True)
        # cols = df_table.columns.drop("date_outage")
        cols = df_table.columns
        df_table[cols] = df_table[cols].apply(pd.to_numeric)
        df_numeric = df_table.select_dtypes(exclude=["object"])
        df_numeric.sort_values("cluster", ascending=True, inplace=True)
        df_numeric.columns = df_numeric.columns.map(lambda x: x.replace("_", " "))
        df_numeric.prediction = df_numeric.prediction*100
        df_numeric = movecol(df_numeric, cols_to_move=["cluster", "prediction"], ref_col="storm duration",place='Before')
        tables.append(df_numeric)
    cols = [
        {
            "name": i,
            "id": i,
            "type": "numeric",
            "format": formato_int if i in ["cluster", "label", "line"] else formato,
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
    p_value = "{:.1f}%".format(filter_prediction_df.prediction.max() * 100)
    df_final = pd.concat(tables, axis=0)
    # print('columns',df_final_changed.columns)
    data_tabla = df_final.to_dict("records")

    return (
        p_value,
        data_tabla,
        cols,
        style_data_conditional,
    )


# print('La figura',get_realtime_figure()
@app.callback(
    Output("cluster-realtime-graph", "figure"),
    Output("datatable-prediction", "data"),
    Output("datatable-prediction", "columns"),
    Output("datatable-prediction", "style_data_conditional"),
    Input("checklist-linea", "value"),
)
def update_graph(lista_linea):
    # print("check listtt ", lista_linea)
    figure = get_realtime_figure(lista_linea)
    p_value, data_tabla, cols, style_data_conditional = get_table(lista_linea)
    return figure, data_tabla, cols, style_data_conditional


@app.callback(
    Output("hora", "children"),
    # Output("card-prob-1", "children"),
    # Output("datatable-prediction", "data"),
    # Output("datatable-prediction", "columns"),
    # Output("datatable-prediction", "style_data_conditional"),
    [
        Input("real-time-interval", "n_intervals"),
    ],
)
def update_graph(num):
    print("""update every 30 seconds""")
    if num == 0:
        raise PreventUpdate
    else:
        filter_prediction_df = filter_prediction_dict[1]
        # print("ensayooo", filter_prediction_df.head())
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
        return (dt.now()-timedelta(hours=5)).strftime("%H:%M:%S")
        # "{:.1f}%".format(filter_prediction_df.prediction.max() * 100),
        # df_numeric.to_dict("records"),
        # cols,
        # style_data_conditional,
