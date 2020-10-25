import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import dash_table_experiments as dt
from functools import lru_cache
import datetime

from app import app,cache




def year_maker(row):
    now_year=int(str(datetime.datetime.now())[:4])
    if row['Закупка']==0:
        return 'Утеряна летопись'
    elif now_year- row['Закупка']<=3:
        return 'до 3 лет'
    elif now_year-row['Закупка']<=5:
        return 'до 5 лет'
    elif now_year- row['Закупка']<=7:
        return 'до 7 лет'
    elif now_year- row['Закупка']>7:
        return 'более 7 лет'

@cache.memoize()
def it_get_df(date):
            
    df=pd.read_excel('all_it.xls',encoding='utf-8')
    #меняем пустые строки на 0
    df=df.fillna(0)
    return df
  



def layout():
    
    
    load_time=str(datetime.datetime.now())
    load_time=load_time[:15]
        
    main_df=it_get_df(load_time)
   
    departments=main_df[main_df['Филиал']!=0]['Филиал'].unique().tolist()
    departments.append('Все')
    return html.Div([
    
    html.Div([html.H3('RGS IT devices' )],style={'text-align':'center', 'font-size': '1.875em'}),
    html.Div(id='all_stored_data',children=load_time,style={'display':'none'}),
   
    html.Div([
         html.Div([dcc.Dropdown(id='all_department',options=[{'label' : i, 'value' : i } for i in departments],value='Все')],style={'width':'100%','display':'inline-block','text-align':'center'})
        
    ]),
    
    html.Div([dcc.Graph(id='all_main_view')
                        ], style={'width': '100%', 'display': 'inline-block'}),
    
    html.Div([dcc.Graph(id='all_age')],style={'width': '49%', 'display': 'inline-block'}),
    html.Div([html.P(id='all_table_info',style={ 'font-size': '1.2em'}),dt.DataTable(rows=[{}],
        # optional - sets the order of columns
        columns=['Наименование','Количество'],
        row_selectable=False,
        #filterable=True,
        sortable=True,
        editable=False,
        id='all_device_info'
        )],style={'width': '49%', 'display': 'inline-block'})
    ]) 


@app.callback(
dash.dependencies.Output('all_main_view','figure'),
[dash.dependencies.Input('all_stored_data','children')
,dash.dependencies.Input('all_department','value')
])

def all_update_main_view(stored_data,department):
    
    main_df=it_get_df(stored_data)
    
    if department!='Все':
        main_df=main_df[main_df['Филиал']==department]
    
    
    main_df=main_df[['Тип оборудования', 'Филиал']].groupby(['Тип оборудования']).agg({'Филиал': lambda x: len(x[x!=0])})
    main_df=pd.DataFrame(main_df.to_records())
    
    return { 
                        'data':[
                        #{'x': main_df['Вид оборудования'], 'y': main_df['Фирма'] ,'marker':{'color':'#d0cbd8'}, 'type' : 'bar'  , 'name' : 'Всего оборудования'},                 
                        {'x': main_df['Тип оборудования'], 'y': main_df['Филиал'] ,'marker':{'color':'#41a270'}, 'type' : 'bar' , 'name' : 'В эксплуатации'}
                        ], 
                        'layout':{ 'hovermode' : 'closest',"font": {"size": '0.7em'}}
                        }

@app.callback(
dash.dependencies.Output('all_age','figure'),
[dash.dependencies.Input('all_stored_data','children')
,dash.dependencies.Input('all_department','value')
,dash.dependencies.Input('all_main_view','clickData')
])


def all_update_age_graph(stored_data,department,device_type):
    
    
    main_df=it_get_df(stored_data)
    
    if department!='Все':
        main_df=main_df[main_df['Филиал']==department]
        
    #Фильтруем по типу оборудования
    try:
        device=device_type['points'][0]['x']
    except TypeError:
        device='Принтер'
        
    main_df=main_df[main_df['Тип оборудования']==device]
    
    #добавим новую колонку с годом ввода в эксплуатацию
    main_df['год'] = main_df.apply (lambda row: year_maker (row),axis=1)
        
    main_df=main_df[['год', 'Филиал']].groupby(['год']).agg({'Филиал': lambda x: len(x[x!=0])})
    main_df=pd.DataFrame(main_df.to_records())
    title_text=device + ' в эксплуатации'
    return {
    'data':[go.Pie(labels=main_df['год'],values=main_df['Филиал']
                        ,hoverinfo='label+value+percent'
                        ,textinfo='percent'
                        ,marker={'colors':['rgba(65, 162, 112,0.9)','rgba(65, 162, 112,0.7)','rgba(65, 162, 112,0.5)','rgba(65, 162, 112,0.3)','rgba(65, 162, 112,0.1)']}
                        )]
    ,'layout':{'title': title_text,"font": {"size": '0.7em'}}
    }




@app.callback(
dash.dependencies.Output('all_device_info','rows'),
[dash.dependencies.Input('all_stored_data','children')
,dash.dependencies.Input('all_department','value')
,dash.dependencies.Input('all_main_view','clickData')
,dash.dependencies.Input('all_age','clickData')
])

def all_update_device_info(stored_data,department,device_type,age):
    
    main_df=it_get_df(stored_data)
    
    #Убираем те что не в эксплуатации
    main_df=main_df[main_df['Филиал']!=0]
    
    if department!='Все':
        main_df=main_df[main_df['Филиал']==department]
        
    
        
    #Фильтруем по типу оборудования
    try:
        device=device_type['points'][0]['x']
    except TypeError:
        device='Принтер'
        
    main_df=main_df[main_df['Тип оборудования']==device]
    
    #добавим новую колонку с годом ввода в эксплуатацию
    main_df['год'] = main_df.apply (lambda row: year_maker (row),axis=1)
    
    #Фильтруем по годам в эксплуатации
    try:
        years_old=age['points'][0]['label']
    except TypeError:
        years_old='до 3 лет'
        
    main_df=main_df[main_df['год']==years_old]
    
    main_df=main_df[['Наименование', 'Филиал']].groupby(['Наименование']).agg({'Филиал': lambda x: len(x[x!=0])})
    main_df=pd.DataFrame(main_df.to_records())
    main_df.columns=['Наименование','Количество']
    
    return main_df.to_dict('records')
    
    
@app.callback(
dash.dependencies.Output('all_table_info','children'),
[dash.dependencies.Input('all_department','value')
,dash.dependencies.Input('all_main_view','clickData')
,dash.dependencies.Input('all_age','clickData')
])

def all_update_table_info(department,device_type,age):
    
    label=department + '  '
    
    try:
        device=device_type['points'][0]['x']
    except TypeError:
        device='Принтер'
    
    label=label + device + ' '
    
    try:
        years_old=age['points'][0]['label']
    except TypeError:
        years_old='до 3 лет'
        
    label=label + years_old + ' в эксплуатации'    
    
    return label
    
