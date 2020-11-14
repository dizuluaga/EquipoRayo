import geopandas as gpd
from shapely.geometry import LineString, Point
import data.data_import as di

towers = di.towers
towers_buffer = towers.reset_index(drop=True)
# towers_buffer['geometry'] = [Point(xy) for xy in zip(towers_buffer['longitude'], towers_buffer['latitude'])]

buffer_3km = LineString(towers_buffer["geometry"]).buffer(0.03)
buffer_5km = LineString(towers_buffer["geometry"]).buffer(0.05)

x_buffer_3km, y_buffer_3km = list(buffer_3km.exterior.coords.xy)
x_buffer_5km, y_buffer_5km = list(buffer_5km.exterior.coords.xy)


def buffer_line(distance, towers_buffer=None):
    """[summary]

    Args:
        distance ([type]): [description]

    Returns:
        [type]: [description]
    """    
    towers_buffer = gpd.GeoDataFrame(towers_buffer,
                          geometry=gpd.points_from_xy(towers_buffer.longitude,
                                                      towers_buffer.latitude),
                          crs='EPSG:4326')
    towers_buffer_planas = towers_buffer.to_crs("EPSG:3116")
    buffer_dist = LineString(towers_buffer_planas["geometry"]).buffer(distance * 1000)
    buffer_dist = gpd.GeoDataFrame(geometry=[buffer_dist], crs="EPSG:3116").to_crs(
        "EPSG:4326"
    )
    x_buffer, y_buffer = list(buffer_dist.iloc[0, 0].exterior.coords.xy)
    return x_buffer, y_buffer, buffer_dist
