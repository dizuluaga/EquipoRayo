import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import dash_table_experiments as dt
import datetime
import pymssql
from app import app,cache
import urllib




#DataFrame с продажами новичков
@cache.memoize(timeout=60*10)
def get_noobs_df(date):
    conn = pymssql.connect(host="10.61.0.228", user="so",password="", port=1433,charset='utf8')  
    stmt ='select * from svodka.. an_noobs_sales2'
        
    df=pd.read_sql(stmt,conn)
    return df


def layout():
    load_time=str(datetime.datetime.now())
    load_time=load_time[:16]
    noobs_df=get_noobs_df(load_time)
   
    return html.Div([
        
        html.Div(className='row',children=[  
            html.Div(id='time',children=load_time,style={'display':'none'}),
        
            html.Div(className='col-lg-2'),
            html.Div(className='col-lg-8',children=[
                dcc.Graph(id="noobs_dept")
            ]),
            html.Div(className='col-lg-2')
        ]),
        html.Div(className='row',children=[
            html.Div(className='col-lg-2'),
            html.Div(className='col-lg-4',children=[
               dcc.Graph(id="noobs_personal")]),
            html.Div(className='col-lg-4',children=[
               dcc.Graph(id='skill_progress')]),
            html.Div(className='col-lg-2')
        ])
    ])
    

@app.callback(dash.dependencies.Output('noobs_dept','figure'),
[dash.dependencies.Input('time','children')])

def change_noobs_dept(time):
    
    title="Продажи новых агентов: {}"
    noobs_df=get_noobs_df(time)
    
    '''    
    try:
        rate_df=rate_df[rate_df.queue_name==category['points'][0]['x']]
        title_add=category['points'][0]['x']
    except TypeError:
        title_add=""
        pass
      ''' 
      
      #группируем данные по отделам
    df=noobs_df[['dept','группа','сборы']]
    df=df.pivot_table(index='dept',columns=['группа'],values=['сборы'], aggfunc=sum)
    df=pd.DataFrame(df.to_records())
    
    namelist=['dept','ИФЛ','КАСКО','Остальное']
    df.columns=namelist
   
    
    #КАСКО
    trace1=go.Bar(
    x=df['dept'],
    y=df['КАСКО'],
    name='КАСКО',
    marker={'color':'rgba(244, 244, 81,0.82)'}
    )
    
    
    #ИФЛ
    trace2=go.Bar(
    x=df['dept'],
    y=df['ИФЛ'],
    name='ИФЛ',
    marker={'color':'rgba(77,218,218,0.82)'}
    )
    
    #остальное
    trace3=go.Bar(
    x=df['dept'],
    y=df['Остальное'],
    name='Остальное',
    marker={'color':'rgba(163, 81, 244,0.82)'}
    )
    
    data=[trace1,trace2,trace3]
       
    return { 
                        'data':
                        data
                        ,'layout':{'title' : 'продажи новых агентов','barmode':'stack'}
                        }
    
    
@app.callback(dash.dependencies.Output('noobs_personal','figure'),
[dash.dependencies.Input('time','children'),
dash.dependencies.Input('noobs_dept','clickData')])
def update_noobs_personal(time,dept):
    title="Новые продавцы в {}"
    noobs_df=get_noobs_df(time)
    
    try:
        otdel=dept['points'][0]['x']
    except TypeError:
        otdel=''
        return {}
    
    
          
    #фильтруем по отделу
    
    df=noobs_df[noobs_df['dept']==otdel]
    
      #группируем данные по фио
    df=df[['фио','date','группа','сборы']]
    df=df.pivot_table(index=['фио','date'],columns=['группа'],values=['сборы'], aggfunc=sum)
    df=pd.DataFrame(df.to_records())
    
    
    
    
    
    #namelist=['фио','ИФЛ','КАСКО','Остальное']
    '''
    try:
        df.columns=namelist
    except ValueError:
        pass
    '''
    
    #КАСКО
    try:
        k1=df["('сборы', 'КАСКО')"]
    except KeyError:
        nulllist=[]
        for i in df['фио']:
            nulllist.append(0)
        k1=nulllist
    
    trace1=go.Bar(
    x=df['фио'],
    y=k1,
    name='КАСКО',
    text=df['date'],
    marker={'color':'rgba(244, 244, 81,0.82)'}

    )
    
    
    #ИФЛ
    try:
        k2=df["('сборы', 'ИФЛ')"]
    except KeyError:
        nulllist=[]
        for i in df['фио']:
            nulllist.append(0)
        k2=nulllist
    
    
    trace2=go.Bar(
    x=df['фио'],
    y=k2,
    name='ИФЛ',
    text=df['date'],
    marker={'color':'rgba(77,218,218,0.82)'}
    )
    
    #остальное
    try:
        k3=df["('сборы', 'Остальное')"]
    except KeyError:
        nulllist=[]
        for i in df['фио']:
            nulllist.append(0)
        k3=nulllist
    trace3=go.Bar(
    x=df['фио'],
    y=k3,
    name='Остальное',
    text=df['date'],
    marker={'color':'rgba(163, 81, 244,0.82)'}
    )
    
    data=[trace1,trace2,trace3]
       
    return { 
                        'data':
                        data
                        ,'layout':{'title' : title.format(otdel),'barmode':'stack'}
                        }


@app.callback(
    dash.dependencies.Output('skill_progress','figure'),
    [dash.dependencies.Input('time','children'),
    dash.dependencies.Input('noobs_dept','clickData'),
    dash.dependencies.Input('noobs_personal','hoverData')]
)

def update_skill_progress(time,dept,agent):
    title="{} прогресс продаж"
    noobs_df=get_noobs_df(time)
    
    try:
        otdel=dept['points'][0]['x']
    except TypeError:
        otdel=''
        return {}
    
    
          
    #фильтруем по отделу
    
    df=noobs_df[noobs_df['dept']==otdel]
    

    try:
        agent=agent['points'][0]['x']
    except TypeError:
        agent=''
        return {}
    
    #фильтруем по фио
    df=noobs_df[noobs_df['фио']==agent]


    #группируем данные по фио
    df=df.pivot_table(index='month',columns=['группа'],values=['сборы'], aggfunc=sum)
    df=pd.DataFrame(df.to_records())
    

    
    #КАСКО
    try:
        k1=df["('сборы', 'КАСКО')"]
    except KeyError:
        nulllist=[]
        for i in df['month']:
            nulllist.append(0)
        k1=nulllist
    
    trace1=go.Scatter(
    x=df['month'],
    y=k1,
    name='КАСКО',
    mode='lines+markers',
    marker={'color':'rgba(244, 244, 81,0.82)'}
    )
    
    
    #ИФЛ
    try:
        k2=df["('сборы', 'ИФЛ')"]
    except KeyError:
        nulllist=[]
        for i in df['month']:
            nulllist.append(0)
        k2=nulllist
    
    
    trace2=go.Scatter(
    x=df['month'],
    y=k2,
    name='ИФЛ',
    mode='lines+markers',
    marker={'color':'rgba(77,218,218,0.82)'}
    )
    
    #остальное
    try:
        k3=df["('сборы', 'Остальное')"]
    except KeyError:
        nulllist=[]
        for i in df['month']:
            nulllist.append(0)
        k3=nulllist

    trace3=go.Scatter(
    x=df['month'],
    y=k3,
    name='Остальное',
    mode='lines+markers',
    marker={'color':'rgba(163, 81, 244,0.82)'}
    )
    
    data=[trace1,trace2,trace3]
       
    return { 
                        'data':
                        data
                        ,'layout':{'title' : title.format(agent),'barmode':'stack'}
                        }

