import pandas as pd
from datetime import timedelta

discharges = pd.read_csv('./data/discharges.csv', header=0, delimiter=',', index_col=0,
                         names=['date', 'longitude', 'latitude', 'polarity', 'magnitude', 'current'], parse_dates=['date'])
outages = pd.read_csv('./data/outages.csv', header=0, delimiter=',', index_col=0,
                     names=['date', 'year', 'time', 'cause', 'outages_number', 'r_inf', 'r_sup'], parse_dates=['date'])
towers = pd.read_csv('./data/towers.csv', header=0,
                     delimiter=',', names=['longitude', 'latitude'])

discharges_all_outages = pd.DataFrame(columns=discharges.columns)

def Discharges_before_outage_by_time(outage_date, time_range, min_before=5):
    datetime_f = outage_date - timedelta(minutes=min_before)
    datetime_i = datetime_f - timedelta(minutes=time_range)
    discharges_copy = discharges.copy()
    discharges_before_outage_by_time = discharges_copy[(discharges['date'] > datetime_i) &
                        (discharges_copy['date'] < datetime_f)].reset_index()
    return discharges_before_outage_by_time
