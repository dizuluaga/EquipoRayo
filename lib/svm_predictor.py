import numpy as np
import pandas as pd
import pickle

# perform prediction
def predict_outage(path, pkl_filename, clean_features_df):

    X = np.asarray(clean_features_df)
    X = np.nan_to_num(X)

    with open(path+pkl_filename, 'rb') as file:
        pickle_model = pickle.load(file)
    prediction = pickle_model.predict_proba(X)[:,1]

    return prediction

def create_prediction_df(clean_features_df, prediction, threshold):
    """[create dataframe based on prediction results]

    Args:
        clean_features_df ([dataframe]): [description]
        prediction ([array]): [description]
        threshold ([float]): [description]

    Returns:
        [dataframe]: [description]
    """
    prediction_df = clean_features_df
    prediction_df['prediction'] = prediction
    prediction_df['label'] = prediction_df.apply(lambda row: 1 if row['prediction']>threshold else 0, axis=1)
    filter_prediction_df = prediction_df[prediction_df.time_delta_min<=60]

    return filter_prediction_df