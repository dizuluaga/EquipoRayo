import lib.st_dbscan_model as st_dbscan_model
import lib.features as features
import lib.svm_predictor as svm_predictor
import data.data_import_DB as di_db
import pandas as pd

# ST-DBSCAN
discharges_df, current_datetime = di_db.discharges_last_5hours()
# model parameters
eps1_km = 10 # spatial distance of 10 km
eps2 = 10 # temporal distance of 10 min
min_samples = 5 # min number of dicharges in cluster nuclei
km_per_radian = 6371.0088
eps1 = eps1_km / km_per_radian
 
data_array = st_dbscan_model.data_preparation(discharges_df=discharges_df, current_datetime=current_datetime)
labels = st_dbscan_model.st_dbscan(eps1=eps1, eps2=eps2, min_samples=min_samples, data_array=data_array)
discharges_by_cluster_df = st_dbscan_model.discharges_by_cluster(data_array=data_array, labels=labels, discharges_df=discharges_df)

# FEATURES
# ******* change ************************
df_towers = pd.read_csv(r"C:\Users\USUARIO\Documents\ds4a\project\EquipoRayo\data_all_lines\towers1.csv", header=0
                        ,delimiter=',', index_col=0)
# ****************************************

raw_features_df = features.extract_features(df_discharges=discharges_by_cluster_df, df_towers=df_towers)
clean_features_df = features.clean_features(raw_features_df=raw_features_df)

# SVM PREDICTION
path = r'./predictor/'
pkl_filename = 'SVM_model.pkl'

prediction = svm_predictor.predict_outage(path=path, pkl_filename=pkl_filename, clean_features_df=clean_features_df)
prediction_df = svm_predictor.create_prediction_df(clean_features_df=clean_features_df, prediction=prediction, threshold=0.3)
filter_prediction_df = svm_predictor.filter_predictions(prediction_df=prediction_df)
print(filter_prediction_df)
