import geopandas as gpd
import pandas as pd

def convertir_gdf(df, crs='EPSG:4326'):
    gdf  = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df.longitude, df.latitude
        ),crs=crs
    )
    gdf.to_crs('EPSG:3116')
    return gdf

def extract_features(df_discharges, df_towers):

    groups = df_discharges.groupby('cluster')

    # primary features
    storm_duration = groups['time_delta'].pipe(lambda x: x.max() - x.min())
    temporal_density = groups['date'].count() / storm_duration
    time_delta_min = groups['time_delta'].min()
    magnitude_mean = groups['magnitude'].mean()
    magnitude_max = groups['magnitude'].max()

    # geopandas operations
    gdf_discharges = convertir_gdf(df_discharges)
    auxi = gdf_discharges.dissolve('cluster').convex_hull
    auxi_proj = gdf_discharges.dissolve('cluster').to_crs('EPSG:3116')
    towers_projected = df_towers.pipe(convertir_gdf).to_crs('EPSG:3116')
    poly = auxi.to_crs('EPSG:3116')
    #poli = gpd.GeoDataFrame(geometry=[auxi], crs='EPSG:4326').to_crs('EPSG:3116')

    # secondary features
    area = poly.area/1000000
    spatial_density = groups['date'].count() / area
    distance_centroid = poly.centroid.distance(towers_projected.unary_union)/1000
    distance_polygon = poly.distance(towers_projected.unary_union)/1000
    distance_max = auxi_proj.distance(towers_projected.unary_union)/1000 #change

    raw_features_df = pd.DataFrame(data={'storm_duration':storm_duration, 'temporal_density':temporal_density
                                        ,'time_delta_min':time_delta_min
                                        ,'magnitude_mean':magnitude_mean, 'magnitude_max':magnitude_max
                                        ,'area':area, 'spatial_density':spatial_density
                                        ,'distance_centroid':distance_centroid, 'distance_polygon':distance_polygon
                                        ,'distance_max':distance_max
                                        ,'cluster':storm_duration.index}
                                    ,index=storm_duration.index)

    clean_features_df = raw_features_df[(raw_features_df.cluster > -1)
                                        & (raw_features_df.area > 0)
                                        & (raw_features_df.storm_duration > 0)]
    
    clean_features_df.drop(columns=['cluster'], inplace=True)

    return clean_features_df

def extract_features_ori(df_discharges, df_towers):

    groups = df_discharges.groupby('cluster')

    storm_durations = []
    temporal_densities = []
    time_deltas_min = []
    magnitudes_mean = []
    magnitudes_max = []
    areas = []
    spatial_densities = []
    distances_centroid = []
    distances_polygon = []
    distances_max = []
    cluster_names = []

    for i, group in groups:

        cluster_names.append(i)

        storm_duration = group['time_delta'].max() - group['time_delta'].min()
        storm_durations.append(storm_duration)

        temporal_density = group['date'].count() / storm_duration
        temporal_densities.append(temporal_density)

        time_delta_min = group['time_delta'].min()
        time_deltas_min.append(time_delta_min)

        magnitude_mean = group['magnitude'].mean()
        magnitudes_mean.append(magnitude_mean)

        magnitude_max = group['magnitude'].max()
        magnitudes_max.append(magnitude_max)

        group_gdf = group.pipe(convertir_gdf, crs='EPSG:4326')
        auxi = group_gdf.unary_union.convex_hull
        auxi_proj = group_gdf.to_crs('EPSG:3116')
        #auxi_proj = group_gdf # new
        towers_projected = df_towers.pipe(convertir_gdf).to_crs('EPSG:3116')
        poli = gpd.GeoDataFrame(geometry=[auxi], crs='EPSG:4326').to_crs('EPSG:3116')

        area = poli.area.iloc[0]/1000000
        areas.append(area)

        spatial_density = group['date'].count() / area
        spatial_densities.append(spatial_density)

        distance_centroid = poli.centroid.distance(towers_projected.unary_union).iloc[0]/1000
        distances_centroid.append(distance_centroid)

        distance_polygon = poli.distance(towers_projected.unary_union).iloc[0]/1000
        distances_polygon.append(distance_polygon)

        distance_max = auxi_proj.distance(towers_projected.unary_union).max()/1000
        distances_max.append(distance_max)

    raw_features_df = pd.DataFrame(data={'storm_duration':storm_durations, 'temporal_density':temporal_densities
                                        ,'time_delta_min':time_deltas_min
                                        ,'magnitude_mean':magnitudes_mean, 'magnitude_max':magnitudes_max
                                        ,'area':areas, 'spatial_density':spatial_densities
                                        ,'distance_centroid':distances_centroid, 'distance_polygon':distances_polygon
                                        ,'distance_max':distances_max
                                        ,'cluster':cluster_names}
                                    ,index=cluster_names)

    clean_features_df = raw_features_df[(raw_features_df.cluster > -1)
                                        & (raw_features_df.area > 0)
                                        & (raw_features_df.storm_duration > 0)]
    #clean_features_df = clean_features_df[clean_features_df.area > 0]
    #clean_features_df = clean_features_df[clean_features_df.storm_duration > 0]
    clean_features_df.drop(columns=['cluster'], inplace=True)
 
    return clean_features_df

#def clean_features(raw_features_df):
#    clean_features_df = raw_features_df[raw_features_df.cluster > -1]
#    clean_features_df = clean_features_df[clean_features_df.area > 0]
#    clean_features_df = clean_features_df[clean_features_df.storm_duration > 0]
#    clean_features_df.drop(columns=['cluster'], inplace=True)
#    return clean_features_df


#df_towers = pd.read_csv(r"C:\Users\USUARIO\Documents\ds4a\project\EquipoRayo\data_all_lines\towers1.csv", header=0
#                        , delimiter=',', index_col=0)
#df_discharges = pd.read_csv(r"C:\Users\USUARIO\Desktop\backup EquipoRayo\data\data_all_lines\discharges_by_cluster.csv"
#                            ,header=0, delimiter=',', index_col=0)
#df_discharges = df_discharges[df_discharges.line==1]

#features_df = features(df_discharges=df_discharges, df_towers=df_towers)
#print(features_df)