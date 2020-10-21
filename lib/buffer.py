import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Point
import data.data_import as di

towers = di.towers
#towers = pd.read_csv(r'C:\Users\USUARIO\Documents\ds4a\project\EquipoRayo\data\towers.csv', header=0,
#                     delimiter=',', names=['longitude', 'latitude'])
towers_buffer = towers.iloc[1:240].reset_index(drop=True)
towers_buffer['geometry'] = [Point(xy) for xy in zip(towers_buffer['longitude'], towers_buffer['latitude'])]

buffer_3km = LineString(towers_buffer['geometry']).buffer(0.03)
buffer_5km = LineString(towers_buffer['geometry']).buffer(0.05)

#buffer_3km_json = gpd.GeoDataFrame(geometry=[buffer_3km]).to_json()
#buffer_5km_json = gpd.GeoDataFrame(geometry=[buffer_5km]).to_json()

x_buffer_3km,y_buffer_3km = list(buffer_3km.exterior.coords.xy)
x_buffer_5km,y_buffer_5km = list(buffer_5km.exterior.coords.xy)
#print(x[0],y)
#print(towers_buffer['geometry']).buffer(0.03))#[0]['geometry']['coordinates'])
