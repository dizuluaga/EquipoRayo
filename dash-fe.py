# Libraries
import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from datetime import timedelta

#token = open('pk.eyJ1IjoiZGlhbmFwenA5NiIsImEiOiJja2dlNTUxbWExN2VkMnJxdTdpYmxrcWowIn0.BaVVonTGXIQavJojx-v4sw').read()
diana = 'zapata'
#Read csv
discharges = pd.read_csv('./data/discharges.csv', header=0, delimiter=',', index_col=0,
                         names=['date','longitude','latitude','polarity','magnitude','current'], parse_dates=['date'])
outages = pd.read_csv('./data/outages.csv', header=0, delimiter=',', index_col=0,
                     names=['date','year','time','cause','outages_number','r_inf','r_sup'], parse_dates=['date'])
towers = pd.read_csv('./data/towers.csv', header=0, delimiter=',', names=['longitude','latitude'])

discharges_all_outages = pd.DataFrame(columns=discharges.columns)

def Discharges_before_outage_by_time(outage_date, time_range):
    datetime_f = outage_date - timedelta(minutes=15)
    datetime_i = datetime_f - timedelta(minutes=time_range)
    discharges_before_outage_by_time = discharges[(discharges['date']>datetime_i) &
                        (discharges['date']<datetime_f)].reset_index()
    return discharges_before_outage_by_time

#for i,outage_date in enumerate(outages['date']):
#    discharges_outage = Discharges_before_outage_by_time(outage_date, 20)
#    discharges_all_outages = pd.concat([discharges_all_outages, discharges_outage], axis=0)
#discharges_all_outages

discharges_outage_1 = Discharges_before_outage_by_time(outages['date'][0], 20)

fig = go.Figure()
fig.add_trace(go.Scattermapbox(
    lat=discharges_outage_1.latitude,
    lon=discharges_outage_1.longitude,
    mode='markers',
    marker=go.scattermapbox.Marker(
        size=7,
        color='blue',
        opacity=0.7
    ),
))
fig.add_trace(go.Scattermapbox(
    lat=towers.latitude,
    lon=towers.longitude,
    mode='markers+lines',
    marker=go.scattermapbox.Marker(
        size=7,
        color='black',
        opacity=0.7
    ),
))
fig.update_layout(
    title='Electric discharges of the last 20 minutes',
    autosize=True,
    #hovermode='closest',
    showlegend=False,
    #mapbox_style="open-street-map",
    height=500,
    mapbox=dict(
        style='open-street-map',
    #    accesstoken=mapbox_access_token,
    #    bearing=0,
        center=dict(
            lat=6.73,
            lon=-73.9
        ),
    #    pitch=0,
        zoom=8
    #    style='light'
))









#discharges_scatter = px.scatter_mapbox(discharges_outage_1, lat="latitude", lon="longitude", color='polarity', hover_data=["polarity", "magnitude"],# hover_name="City"],
#                                        title='Electric discharges of the last 20 minutes', zoom=10, height=300)
#discharges_scatter.update_layout(mapbox_style="open-street-map", height=500)

#towers_line = px.line_mapbox(towers, lat='latitude', lon='longitude')
#towers_line.update_layout(mapbox_style="open-street-map", height=500)
#towers_scatter = px.scatter(towers, x="latitude", y="longitude"),# hover_name="City"],                 
#fig.update_layout(mapbox_style="dark", mapbox_accesstoken=token)
#fig.update_layout(mapbox_style="open-street-map")

#towers_scatter = px.scatter_mapbox(towers, lat='longitude', lon='latitude')

#discharges_scatter = px.scatter(towers, x='longitude', y='latitude', color='polarity', hover_data=['longitude', 'latitude',
#                                                                             'polarity', 'magnitude'])

# Application
app = dash.Dash(__name__)

# Layout
app.layout = html.Div(children=[
    html.H1(['Línea Comuneros - Primavera'], id='title'),# Creates the title
    dcc.Graph(id='scatter', figure=fig, style={'width': 700})#dict(data=[discharges_scatter,towers_scatter],
    #layout={mapbox_style='open-street-map'})) #dict(accesstoken=MAPBOX_KEY))#,
    #dcc.Graph(id='towers_line', figure=towers_line)
#    dcc.Graph(id='towers_scatter', figure=towers_scatter)# px)#, clickData=),
#    dash_table.DataTable(id='table',
#                        columns=[{'name':i, 'id':i} for i in df.columns],
#                        data=df.head(5).to_dict('records')
#)
], id='layout')

#mode=‘markers’,
#marker={
#‘size’: 15,
#‘opacity’: 0.5,
#‘line’: {‘width’: 0.5, ‘color’: ‘white’}
#}))
#@app.callback(Output('table', 'data'), [Input('scatter', 'clickData')])
#def changeTable(clickData):
#    print(clickData)
#    try:
#        OrderID = clickData['points'][0]['customdata'][2]
#    except:
#        pass
#    else:
#        ddf = df[df['Order ID']==OrderID]
#        return ddf.head(5).to_dict()

if __name__=='__main__':
    app.run_server(host='0.0.0.0', port='8060', debug=True)
    