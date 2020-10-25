import pandas as pd
from sqlalchemy import create_engine
import os

# Database information from env variables
DATABASES = {
    'db_isa': {
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST'),
        'PORT': os.environ.get('POSTGRES_PORT'),
    },
}

# choose the database to use
db = DATABASES['db_isa']

# construct an engine connection string
engine_string = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}".format(
    user=db['USER'],
    password=db['PASSWORD'],
    host=db['HOST'],
    port=db['PORT'],
    database=db['NAME'],
)

# create sqlalchemy engine
engine = create_engine(engine_string)

# read failures table from database into pandas dataframe
discharges = pd.read_sql_table('tbl_discharges', engine, index_col='id_discharges')
outages = pd.read_sql_table('tbl_outages', engine, index_col='id_outages')
towers = pd.read_sql_table('tbl_towers', engine)

#outages.iloc[0].astype(str)
print('Data import done')
print('worked')
print(outages.dtypes)