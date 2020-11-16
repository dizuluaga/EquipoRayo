import numpy as np
import pandas as pd
from datetime import datetime
from st_dbscan import ST_DBSCAN

# prepares data to be enter to the ST-DBSCAN algorithm
def data_preparation(discharges_df, current_datetime):
    discharges_df['current_datetime'] = current_datetime
    discharges_df['time_delta'] = (current_datetime - discharges_df['date']).dt.total_seconds()/60
    discharges_df['longitude_rad'] = discharges_df.apply(lambda row: np.radians(row['longitude']), axis=1)
    discharges_df['latitude_rad'] = discharges_df.apply(lambda row: np.radians(row['latitude']), axis=1)
    discharges_slice_df = discharges_df[['time_delta','longitude_rad','latitude_rad']].reset_index(drop=True)
    data_array = discharges_slice_df.loc[:,['time_delta','longitude_rad','latitude_rad']].values

    return data_array


#data_preparation

# ST-DBSCAN algorithm
def st_dbscan(eps1, eps2, min_samples, data_array):

    st_dbscan = ST_DBSCAN(eps1=eps1, eps2=eps2, min_samples=min_samples)
    st_dbscan = st_dbscan.fit(data_array)

    return st_dbscan.labels

# creates dataframe that contains discharges information and their cluster assignment based on ST-DBSCAN algorithm
def discharges_by_cluster(data_array, labels, discharges_df):

    data_lon_rad = data_array[:,1]
    data_lat_rad = data_array[:,2]
    data_timedelta = data_array[:,0]
    data_clusters = labels
    dic = {'time_delta':data_timedelta,'longitude_rad':data_lon_rad
            ,'latitude_rad':data_lat_rad,'cluster':data_clusters}
    discharges_by_cluster_df = pd.DataFrame(dic)
    discharges_by_cluster_df.set_index(discharges_df.index, inplace=True)
    discharges_by_cluster_df = discharges_by_cluster_df.merge(discharges_df[['date','longitude','latitude','polarity'
                                                                            ,'magnitude','current','line']]
                                                            ,how='inner', left_index=True, right_index=True)

    return discharges_by_cluster_df


#eps1_km = 10 # spatial distance of 10 km
#eps2 = 10 # temporal distance of 10 min
#min_samples = 5 # min number of dicharges in cluster nuclei

#km_per_radian = 6371.0088
#eps1 = eps1_km / km_per_radian
 
#data_array = data_preparation(discharges_df, working_datetime)
#labels = st_dbscan(eps1=eps1, eps2=eps2, min_samples=min_samples, data_array=data_array)
#discharges_by_cluster_df = discharges_by_cluster(data_array=data_array, labels=labels, discharges_df=discharges_df)