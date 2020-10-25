import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import dash_table_experiments as dt
import datetime
import pymysql
from app import app,cache
import urllib




'''
#Подключение к бд
connection = pymysql.connect(host='10.61.0.32',
                             user='adm',
                             password='qwerty016123',
                             db='otrs',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

'''


#DataFrame с средним ожиданием по очередям
@cache.memoize()
def get_q_avg_df(date):
    conn = pymysql.connect(host="10.61.0.32", user="adm",password="qwerty016123", port=3306,charset='utf8',db='otrs')  
    stmt = """select queue_id as q_id,(select name from queue where queue.id=q_id) as queue_name,
    sum(datediff(change_time,create_time))/(select count(queue_id) from ticket where queue_id=q_id) as avg_days_to_solve_problem
    from ticket
    group by q_id,queue_name"""
        
    df=pd.read_sql(stmt,conn)
    return df

#DataFrame с количеством обращений по юзерам
@cache.memoize()
def get_rating_df(date):
    conn = pymysql.connect(host="10.61.0.32", user="adm",password="qwerty016123", port=3306,charset='utf8',db='otrs')  
    stmt = """select distinct customer_id as client,queue_id as q_id,(select name from queue where queue.id=q_id) as queue_name,
    (select count(customer_id) from ticket where customer_id=client and queue_id=q_id) as tickets 
    from ticket
    order by tickets desc"""
        
    df=pd.read_sql(stmt,conn)
    return df

#DataFrame с открытыми заявками
@cache.memoize()
def get_open_df(date):
    conn = pymysql.connect(host="10.61.0.32", user="adm",password="qwerty016123", port=3306,charset='utf8',db='otrs')  
    stmt = """select queue_id as q_id,tn,(select name from queue where queue.id=q_id) as queue_name ,datediff(now(),create_time) as days_in_process
    from ticket
    where ticket_state_id=1 and datediff(now(),create_time)>3
    order by days_in_process"""
        
    df=pd.read_sql(stmt,conn)
    return df



def layout():
    load_time=str(datetime.datetime.now())
    load_time=load_time[:16]
    avg_df=get_q_avg_df(load_time)
    rate_df=get_rating_df(load_time)
    open_df=get_open_df(load_time)
    
    return html.Div([
        html.Div(className='row',children=[
    
            html.Div(id='time',children=load_time,style={'display':'none'}),
    
            html.Div(className='col-lg-6',children=[
                dcc.Graph(id="avg_graph",figure={
                'data' : [{'x':avg_df.queue_name.tolist(),'y':avg_df.avg_days_to_solve_problem.tolist(),
                'type' : 'bar' ,'marker':{'color':'rgba(255, 51, 51,0.5)'}}]
                ,'layout':{'title' : "Среднее количество дней на обслуживание заявки по категориям"}
                })
            ]),
        
            html.Div(className='col-lg-6',children=[
        
                 dcc.Graph(id="user_pie",figure={
                 'data' : [go.Pie(labels=rate_df.client.tolist(),values=rate_df.tickets.tolist(), 
                
                 hoverinfo='label+value+percent',
                 textinfo='none' )], 'layout' : {'title' : "Количество обращений"}
                })
        
            ])
        ]),
        html.Div(className='row',children=[
            html.Div(className='col-lg-12',children=[
                dt.DataTable(rows=open_df.to_dict('records'),

                # optional - sets the order of columns
                columns=['tn','queue_name','days_in_process'],

                row_selectable=False,
                filterable=False,
                sortable=True,
                editable=False,
                id='open_tickets')
            ])
        ])
    ])
    

@app.callback(dash.dependencies.Output('user_pie','figure'),
[dash.dependencies.Input('time','children'),
dash.dependencies.Input('avg_graph','clickData')])

def change_user_pie(time,category):
    
    title="Количество обращений по категории: {}"
    rate_df=get_rating_df(time)
        
    try:
        rate_df=rate_df[rate_df.queue_name==category['points'][0]['x']]
        title_add=category['points'][0]['x']
    except TypeError:
        title_add=""
        pass
        
   
    
    return {
            'data' : [go.Pie(labels=rate_df.client.tolist(),values=rate_df.tickets.tolist(), 
                
            hoverinfo='label+value+percent',
            textinfo='none' )], 'layout' : {'title' : title.format(title_add)}
            }
    
    
