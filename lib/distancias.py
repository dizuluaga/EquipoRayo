import os
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine


def convertir_gdf(df, crs='EPSG:4326'):
    gdf  = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df.longitude, df.latitude
        ),crs=crs
    )
    gdf.to_crs('EPSG:3116')
    return gdf

class FeaturesDistancia:
    def __init__(self, df_training, df_towers):
        self.df_training = df_training
        self.df_towers =  df_towers
        
    def distancias_maximas(self):
        distancias_dict={}
        for cluster_id in self.df_training.clusters.unique():
            auxi = self.df_training[self.df_training['clusters']==cluster_id].pipe(convertir_gdf, crs='EPSG:4326').to_crs('EPSG:3116')
            towers_projected = self.df_towers.pipe(convertir_gdf).to_crs('EPSG:3116')
            distancia = auxi.distance(towers_projected.unary_union).max()
            distancias_dict[cluster_id] = distancia
        df = pd.DataFrame.from_dict(distancias_dict, orient='index', columns=['dist_puntos_max'])#.to_excel(f'training_dist_puntos_max_{i+1}.xlsx')
        return df
        
    def distancias_minimas(self):   
        distancias_dict={}
        for cluster_id in self.df_training.clusters.unique():
            auxi = self.df_training[self.df_training['clusters']==cluster_id].pipe(convertir_gdf, crs='EPSG:4326').to_crs('EPSG:3116')
            towers_projected = self.df_towers.pipe(convertir_gdf).to_crs('EPSG:3116')
            distancia = auxi.distance(towers_projected.unary_union).min()
            distancias_dict[cluster_id] = distancia
        df = pd.DataFrame.from_dict(distancias_dict, orient='index', columns=['dist_puntos_min'])#.to_excel(f'training_dist_puntos_min_{i+1}.xlsx')
        return df
        
    def distancias_poligono(self):   
        distancias_dict={}
        for cluster_id in self.df_training.clusters.unique():
            auxi = self.df_training[self.df_training['clusters']==cluster_id].pipe(convertir_gdf, crs='EPSG:4326').unary_union.convex_hull
            towers_projected = self.df_towers.pipe(convertir_gdf).to_crs('EPSG:3116')
            poli = gpd.GeoDataFrame(geometry=[auxi], crs='EPSG:4326').to_crs('EPSG:3116')
            distancia = poli.distance(towers_projected.unary_union).iloc[0]
            distancias_dict[cluster_id] = distancia
        df = pd.DataFrame.from_dict(distancias_dict, orient='index', columns=['dist_poligono'])#.to_excel(f'training_dist_poligono_{i+1}.xlsx')
        return df
        
    def distancias_centroide(self):   
        distancias_dict={}
        for cluster_id in self.df_training.clusters.unique():
            auxi = self.df_training[self.df_training['clusters']==cluster_id].pipe(convertir_gdf, crs='EPSG:4326').unary_union.convex_hull
            towers_projected = self.df_towers.pipe(convertir_gdf).to_crs('EPSG:3116')
            poli = gpd.GeoDataFrame(geometry=[auxi], crs='EPSG:4326').to_crs('EPSG:3116')
            distancia =poli.centroid.distance(towers_projected.unary_union).iloc[0]
            distancias_dict[cluster_id] = distancia
        df = pd.DataFrame.from_dict(distancias_dict, orient='index', columns=['dist_centro'])#.to_excel(f'training_dist_centro_{i+1}.xlsx')
        return df
    
    def areas(self): 
        areas_dict={}
        for i in self.df_training.clusters.unique():
            auxi = self.df_training[self.df_training['clusters']==i].pipe(convertir_gdf, crs='EPSG:4326').unary_union.convex_hull
            poli = gpd.GeoDataFrame(geometry=[auxi], crs='EPSG:4326')
            areas_dict[i] = poli.to_crs('EPSG:3116').area.iloc[0]
        df = pd.DataFrame.from_dict(areas_dict, orient='index', columns=['Area_metros'])#.to_excel('training_areas_1.xlsx')
        return df