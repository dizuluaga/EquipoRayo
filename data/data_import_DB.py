# Libraries
import dash
from dash.dependencies import Input, Output, State
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

import pandas as pd
from sqlalchemy import create_engine
import os

credenciales = dict(
    POSTGRES_DB="db_isa",
    POSTGRES_USER="postgres",
    POSTGRES_PASSWORD="ninguna.123",
    POSTGRES_HOST="extended-case-4.crccn2eby4ve.us-east-2.rds.amazonaws.com",
    POSTGRES_PORT=5432,
)

# Database information from env variables
DATABASES = {
    "db_isa": {
        "NAME": credenciales.get("POSTGRES_DB"),
        "USER": credenciales.get("POSTGRES_USER"),
        "PASSWORD": credenciales.get("POSTGRES_PASSWORD"),
        "HOST": credenciales.get("POSTGRES_HOST"),
        "PORT": credenciales.get("POSTGRES_PORT"),
    },
}

# choose the database to use
db = DATABASES["db_isa"]

# construct an engine connection string
engine_string = (
    "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}".format(
        user=db["USER"],
        password=db["PASSWORD"],
        host=db["HOST"],
        port=db["PORT"],
        database=db["NAME"],
    )
)

# create sqlalchemy engine
engine = create_engine(engine_string)

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


def get_discharges(date_first="2018-04-05", num_days=1, table_id=1):
    df = pd.read_sql_query(
        f"""SELECT * FROM tbl_discharges_{table_id}
                        WHERE date BETWEEN ('{date_first}'::date - interval '{num_days} days') AND ('{date_first}'::date + interval '{num_days} days') """,
        engine,
    )
    return df


@app.callback(
    [
        Output("memory-outages", "data"),
    ],
    [
        Input(component_id="power_line_name", component_property="value"),
    ],
)
def filter_outages(power_line_name):
    table_id = lineas_dict_numbers[power_line_name]
    outages = pd.read_sql_table(f"tbl_outages_{table_id}", engine)
    return (outages.to_dict("records"),)


@app.callback(
    [
        Output("memory-towers", "data"),
    ],
    [
        Input(component_id="power_line_name", component_property="value"),
    ],
)
def filter_towers(power_line_name):
    table_id = lineas_dict_numbers[power_line_name]
    towers = pd.read_sql_table(f"tbl_towers_{table_id}", engine)
    return (towers.to_dict("records"),)


@app.callback(
    [
        Output("memory-discharges", "data"),
    ],
    [
        Input(component_id="power_line_name", component_property="value"),
        Input("outage_dropdown", "value")
    ],
    [State("memory-outages", "data")],
)
def filter_towers(power_line_name, outage_indicator,data_outages):
    outages = pd.DataFrame.from_dict(data_outages)
    table_id = lineas_dict_numbers[power_line_name]
    outages = pd.read_sql_table(f"tbl_outages_{table_id}", engine)
    outages["date"] = pd.to_datetime(outages["date"])
    outage_date = outages.loc[int(outage_indicator), "date"]
    print("Indicador", outage_indicator)
    discharges = get_discharges(date_first=outage_date, num_days=2, table_id=table_id)
    return (discharges.to_dict("records"),)


# # Original
# @app.callback(
#     [
#         Output("memory-towers", "data"),
#         Output("memory-outages", "data"),
#         Output("memory-discharges", "data"),
#     ],
#     [
#         Input(component_id="power_line_name", component_property="value"),
#         Input("outage_dropdown", "value")
#     ],
# )
# def filter_countries(power_line_name, outage_indicator):
#     # if not countries_selected:
#     #     # Return all the rows on initial load/no country selected.
#     #     return df.to_dict("records")
#     table_id = lineas_dict_numbers[power_line_name]
#     # print('Holaaaa')
#     towers = pd.read_sql_table(f"tbl_towers_{table_id}", engine)
#     outages = pd.read_sql_table(f"tbl_outages_{table_id}", engine)
#     outages["date"] = pd.to_datetime(outages["date"])
#     print("Indicador", outage_indicator)
#     outage_date = outages.loc[int(outage_indicator), "date"]
#     print(outage_date)
#     discharges = get_discharges(date_first=outage_date, num_days=2, table_id=table_id)
#     print("Memory", discharges.head(2))
#     return (
#         towers.to_dict("records"),
#         outages.to_dict("records"),
#         discharges.to_dict("records"),
#     )
