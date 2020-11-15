import numpy as np
import pandas as pd
import pickle

#***change path*****
#path = r'C:/Users/USUARIO/Documents/ds4a/project/EquipoRayo/predictor/'
#features_df = pd.read_csv(r'C:\Users\USUARIO\Documents\ds4a\project\EquipoRayo\data_all_lines\features.csv', header=0
#                            , delimiter=',',index_col=0, encoding='utf-8-sig')
#features_df = features_df.loc[:4,:]
#print(features_df)
#******************

#path = './predictor/'
#pkl_filename = 'SVM_model.pkl'

def predict_outage(path, pkl_filename, clean_features_df):

    X = np.asarray(clean_features_df)
    X = np.nan_to_num(X)

    with open(path+pkl_filename, 'rb') as file:
        pickle_model = pickle.load(file)
    prediction = pickle_model.predict_proba(X)[:,1]

    return prediction

def create_prediction_df(clean_features_df, prediction, threshold):

    prediction_df = clean_features_df
    prediction_df['prediction'] = prediction
    prediction_df['label'] = prediction_df.apply(lambda row: 1 if row['prediction']>threshold else 0, axis=1)

    return prediction_df

def filter_predictions(prediction_df):
    filter_prediction_df = prediction_df[prediction_df.time_delta_min<=60]
    return filter_prediction_df
    #prediction_df['cluster'] = prediction_df.index
    #discharges_by_cluster_predic_df = discharges_by_cluster_df.merge(prediction_df, how= ,on='cluster')
    #return discharges_by_cluster_predic_df

#prediction = predict_outage(path=path, pkl_filename=pkl_filename, features_df=features_df)
#prediction_df(features_df=features_df, prediction=prediction, threshold=0.55)
#print(prediction_df)
