#!/usr/bin/env python3
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import pymssql
import os
import datetime
import dash_table_experiments as dt
import operator
from app import app,cache
from flask import jsonify

def paint_col(row,col_name):
    '''return rgba color-code
    by col_name value'''
    if row[col_name]<70:
        result='rgba(229,87,81,0.8)'
    elif row[col_name]>=70 and row[col_name]<90:
        result='rgba(255,195,0,0.8)'
    else:
        result='rgba(87,199,133,0.8)'
    return result


def group_maker(row,df):
    ''' Возвращает название группы к 
    которой относится вид страхования'''

    if row.vid in ['04. НС ФЛ', '05. НС ЮЛ', '36. НС Фортуна Авто', '38. НС Фортуна Авто 2']:
        result='НС'
    elif row.vid in ['14. Строения', '15. Квартиры']:
        result='ИФЛ'
    elif row.vid in ['08. КАСКО ФЛ', '09. КАСКО ЮЛ']:
        result='КАСКО'
    else :
        result='Остальное'
    return result



def col_maker(row,pp_df,col_name):
    '''вставляет колонку
    в отфильтрованный DataFrame 
    из отфильтрованного DataFrame по виду страхования'''
    pp_df=pp_df[pp_df.vid==row.vid]
    try:
        result=pp_df.ix[:,col_name].sum()
    except KeyError:
        result=0
    return result



def week_plan_maker(row,quarter,week,week_num,plan_df,main_df):
    '''считает размер недельного плана по виду страхования'''
    #фильтруем по виду
    plan_df=plan_df[plan_df.vid==row.vid]
    main_df=main_df[main_df.vid==row.vid]

    plan=0
    #еженедельная доля текущего квартала в зависимости от номера недели
    plan+=plan_df[plan_df['quarter']==quarter]['plan'].sum()*week_num/13
    #недобор за прошлые периоды. Сумма плана всех кварталов, кроме текущего - все поступления кроме текущей недели 
    plan+=(plan_df[plan_df['quarter']<quarter]['plan'].sum()-main_df[main_df['week']<week]['fact_rub'].sum())
    return plan



def plan_maker(row,plan_df,quarter_list):
    '''вставляет план
    в отфильтрованный DataFrame с фактом
    из отфильтрованного DataFrame с планом'''
    plan_df=plan_df[plan_df.vid==row.vid]
    result=0
    for quarter in quarter_list:
        result+=plan_df[plan_df['quarter']==quarter].ix[:,'plan'].sum()/3
    return result






def get_m_q(months):
    '''получает 2 месяца в виде [1,n] и возвращает
    полный список месяцов между ними и список
    соответствующих месяцам кварталов'''
    month_list=[]
    quarter_list=[]
    for i in range(months[0],months[1]+1):
        if i<=3:
            q=1
        elif i>3 and i <=6:
            q=2
        elif i>6 and i <=9:
            q=3
        elif i>9 and i<=12:
            q=4
        else:q=0
        month_list.append(i)
        quarter_list.append(q)
    return month_list,quarter_list

def generate_table(df,max_rows):
    '''превращает Dataframe в html-таблицу с указанным количеством строк'''
    return html.Table(className='table table-striped table-sm table-bordered small',children=[
    #Header
    html.Thead(children=[html.Tr([html.Th(col) for col in df.columns])]),
    #Body
    html.Tbody(children=[html.Tr([
        html.Td(df.iloc[i][col]) for col in df.columns]) for i in range(min(len(df),max_rows))])])



def filter_corp_vidi(df):
    '''оставляет в DataFrame только виды корпоративного страхования'''
    corp_vidi=['02','05','09','11','13','18','19','20','21','22','23','24','25','26','27','29','30','31','34','37']
    vidi=df.vid.unique()
    for vid in vidi:
        if vid[:2] not in corp_vidi:
            df=df[df.vid!=vid]
    return df

def filter_corp_vidi_s_osago(df):
    '''оставляет в DataFrame только виды корпоративного страхования + ОСАГО ЮЛ'''
    corp_vidi=['02','05','09','11','13','18','19','20','21','22','23','24','25','26','27','29','30','31','34','37','07']
    vidi=df.vid.unique()
    for vid in vidi:
        if vid[:2] not in corp_vidi:
            df=df[df.vid!=vid]
    return df


@cache.memoize(timeout=10*60)
def get_fact_df(date):
    '''получает из БД и кеширует DataFrame с поступлениями'''
    conn = pymssql.connect(server="10.61.0.228", user="so",password="", port=1433,charset='utf8')  
    stmt = "SELECT * FROM  svodka..an_fact"
        
    df=pd.read_sql(stmt,conn)
    huevi_vidi=['01. Жизнь ФЛ','02. Жизнь ЮЛ','03. ИСЖ','35. МАРС']
    df=df[~(df['vid'].isin(huevi_vidi))]

    return df
  

@cache.memoize(timeout=10*60)
def get_vid_df(date):
    '''получает из БД и кеширует DataFrame с видами'''
    conn = pymssql.connect(server="10.61.0.228", user="so",password="", port=1433,charset='utf8') 
    stmt = "SELECT * FROM  svodka..an_vid"
        
    df=pd.read_sql(stmt,conn)
    return df




@cache.memoize(timeout=10*60)
def get_plan_df(date):
    '''получает из БД и кеширует DataFrame с планом'''
    conn = pymssql.connect(server="10.61.0.228", user="so",password="", port=1433,charset='utf8')
    stmt = "SELECT * FROM  svodka..an_plan"
        
    df=pd.read_sql(stmt,conn)
    df=df[df['plan']>0]
    return df

@cache.memoize(timeout=10*60)
def get_fact_pp_df(date):
    '''получает из БД и кеширует DataFrame с поступлениями прошлого периода'''
    conn = pymssql.connect(server="10.61.0.228", user="so",password="", port=1433,charset='utf8')  # You can lookup the port number inside SQL server.
    stmt = "SELECT * FROM  svodka..an_fact_pp"
        
    df=pd.read_sql(stmt,conn)
    #df=df[df['fact_pp']>0]
    return df


def layout():
    '''формирует html код страницы'''
    
    load_time=str(datetime.datetime.now())
    load_time=load_time[:15]
        
    main_df=get_fact_df(load_time)
    #Итоговая строка
    itog_row=pd.DataFrame({'otdel' : [' Итого'],
     'mk' : [' Итого']})
    main_df=main_df.append(itog_row)
    main_df=main_df.sort_values(['otdel'],ascending=[1])

    #загрузим ради кеширования все данные из бд
    pp_df=get_fact_pp_df(load_time)
    plan_df=get_plan_df(load_time)
    vid_df=get_vid_df(load_time)
    
    
    return (
            #control panel
            html.Ul(className='col-lg-2 left-pan',children=[

                html.Br(),
                html.Br(),


                html.Div(className='page-header',children=[
                    html.H5('Канал продаж :'),
                    dcc.RadioItems(
                        id='data_type',
                        options=[{'label': i, 'value': i} for i in ['Розница', 'Корпоратив']],
                        value='Розница'
                        ,labelStyle={'display': 'block'}
                    )
                ]),

                html.Div(className='page-header',children=[
                    html.H5('Год :'),
                    dcc.Dropdown(id='drop_year',options=[{'label' : i, 'value' : i } for i in main_df.year.unique()],value=main_df.year.max())
                ]),
                html.Div(className='page-header',children=[
                    html.H5('Группировка :'),
                    dcc.Dropdown(id='drop_otdel',options=[{'label' : i, 'value' : i } for i in ['Без Дирекции','Все']],value='Все')
                ]),
                html.Div(className='page-header',children=[
                    html.H5('Отдел :'),
                    dcc.Dropdown(id='drop_so',options=[{'label' : i, 'value' : i } for i in main_df.otdel.unique()],value=' Итого')
                ]),
                html.Div(className='page-header',children=[
                    html.H5('Малый канал :'),
                    dcc.Dropdown(id='drop_mk',options=[{'label' : i, 'value' : i } for i in main_df.mk.unique()],multi=True,value=' Итого')
                ]),

                #load time as key value for redis
                html.Div(id='stored_data',children=load_time,style={'display':'none'}),
                html.Div(className='page-header',children=[
                    html.H5('Месяц :'),
                    dcc.RangeSlider(
                        id='month',
                        marks={i: '{}'.format(i) for i in range(1,13)},
                        min=1,
                        max=12,
                        value=[1,pp_df.month.max()]
                        
                        ),
                    html.Br()   
                    
                ]),
                
                html.Div(className='page-header',children=[
                    html.H5('Недельное задание :'),
                    dcc.Checklist(id='week_type',options=[{'label' : ' Отобразить выполнение недельного задания', 'value' : 'yes' }],values=[])
                ])
           
            ])
        ,
        #bs row with page title
        html.Div(className='row',children=[
            html.Div(className='col-lg-2'),
            html.Div(className='col-lg-10',children=html.H4(className='page-header center-text',children='Выполнение плана по данным сводки')),
            html.Div(className='col-lg-2')]
        ),
        #bs row with content
        html.Div(className='row',children=[

            html.Div(className='col-lg-2'),
            
            #graphs
            html.Div(className='col-lg-10',children=[
                html.Div(className='col-lg-12',children=[dcc.Graph(id='vp_motivation')])
                ,html.Div(className='col-lg-12',children=[dcc.Graph(id='weeks_dynamic')])
                ,html.Div(className='col-lg-6',children=[dcc.Graph(id='vp_mk')])
                ,html.Div(className='col-lg-6',children=[dcc.Graph(id='vp_port')])
                ,html.Div(className='col-lg-12',id='vp_vid')
            ]),

            html.Div(className='col-lg-2')
        ]) 
    )


@app.callback(
    dash.dependencies.Output('drop_so','value'),
    [dash.dependencies.Input('vp_motivation','clickData')]
)
def update_drop_so_value(some):
    '''меняет значение выпадающего списка
    со страховым отделом по клику на столбце'''
    try:
        otdel=some['points'][0]['x']
    except TypeError:
        otdel=' Итого'
    return otdel


@app.callback(
    dash.dependencies.Output('drop_mk','value'),
    [dash.dependencies.Input('vp_mk','clickData')]
)

def update_drop_mk_value(some):
    '''меняет значение выпадающего списка
    с малыми каналами по клику на столбце'''
    try:
        mk=some['points'][0]['x']
    except TypeError:
        mk=' Итого'
    return mk



@app.callback(
    dash.dependencies.Output('vp_motivation', 'figure'),
    
    [dash.dependencies.Input('stored_data', 'children'),
     dash.dependencies.Input('data_type', 'value'),
     dash.dependencies.Input('drop_year', 'value'),
     dash.dependencies.Input('drop_otdel', 'value'),
     dash.dependencies.Input('drop_mk','value'),
     dash.dependencies.Input('month', 'value')]         
)
    
    
def update_main_graph(load_time,data_type,year,drop_otdel,mk_in,months):
    '''Процедура обновления основного графика
    с выполнением плана по отделам'''

    #получаем все данные
    main_df=get_fact_df(load_time)
    plan_df=get_plan_df(load_time)
    
    
    
    
    if data_type=='Корпоратив':
        main_df=filter_corp_vidi(main_df)
        plan_df=filter_corp_vidi(plan_df)


    
    #Выбор группы отделов согласно значения drop_otdel
    if drop_otdel=='Без Дирекции' :
        main_df=main_df[~(main_df.otdel.str.startswith('Дирекция', na=False))]
        plan_df=plan_df[~(plan_df.otdel.str.startswith('Дирекция', na=False))]
    
    
        
    
    #отбираем виды для расчета выполнения мотивационного плана
    
    huevi_vidi=['06. ОСАГО ФЛ','07. ОСАГО ЮЛ','90. ИСЖ','91. НСЖ']
   
    #убираем виды не входящие в мотивацию из main_df
    for vid in huevi_vidi:
        main_df=main_df[main_df.vid!=vid]
        plan_df=plan_df[plan_df.vid!=vid]
       
    

    #фильтр по месяцам
    month_list,quarter_list=get_m_q(months)
    plan_df=plan_df.astype({'quarter':'int'})
    main_df=main_df[main_df['month'].isin(month_list)]
    plan_df=plan_df[plan_df['quarter'].isin(quarter_list)]
   
    

    #Фильтруем по мк
    mk=[]
    if isinstance(mk_in,list):
        if len(mk_in)>0 and mk_in!=[' Итого']:
            for x in mk_in:
                if x!=' Итого':
                    mk.append(x)
        elif len(mk_in)==0:
            mk=[]    
        else: 
            mk.append(' Итого')
    else:
        mk.append(mk_in)
        
    
    if mk!=[' Итого']:
        main_df=main_df[main_df.mk.isin(mk)]
        plan_df=plan_df[plan_df.mk.isin(mk)]


    
    #добавим Итого в  наборы данных
    
    itog_row=pd.DataFrame({'otdel' : [' Итого'],
     'mk' : [' Итого']})
    main_df=main_df.append(itog_row)
    plan_df=plan_df.append(itog_row)
    
    
    #список отделов с итого
    
    otdel_spisok=plan_df.otdel.unique()    
    

    
       
    vp_otdel=[]   
    i=0
    
    
    for a in otdel_spisok :
        plan=0
        if a==' Итого':
            sorry=main_df
            sorry_plan=plan_df
        else:
            sorry=main_df[(main_df['otdel']==a)]
            sorry_plan=plan_df[plan_df['otdel']==a]
        
        for q in quarter_list:
            plan+=(sorry_plan[sorry_plan.quarter==q].ix[:,'plan'].sum())/3
            
            


        if plan>0:
            vp_otdel.append(int((sorry.ix[:,'fact_rub'].sum()/(plan))*100))
        else:  vp_otdel.append(0)
        i+=1
           
    vp_data_df= pd.DataFrame()
    vp_data_df['otdel']=otdel_spisok
    vp_data_df['vp']=vp_otdel
    vp_data_df['color']=vp_data_df.apply(lambda row: paint_col(row,'vp'),axis=1)
    
    vp_data_df=vp_data_df.sort_values(by=['vp'])


        
    
    #возвращаем график
    return { 
                        'data':[{
                         'x': vp_data_df.otdel,
                         'y': vp_data_df.vp ,
                         'type' : 'bar' ,
                         'name' : 'выполнение плана',
                         'marker' : {'color':vp_data_df.color}
                         }]
                        ,'layout':{'title' : '% выполнения мотивационного плана','hovermode' : 'closest'}
                        }






@app.callback(
     dash.dependencies.Output('vp_vid','children'),
     [dash.dependencies.Input('stored_data', 'children'),
     dash.dependencies.Input('data_type', 'value'),
     dash.dependencies.Input('drop_so','value'),
     dash.dependencies.Input('drop_mk','value'),
     dash.dependencies.Input('drop_year', 'value'),
     dash.dependencies.Input('drop_otdel', 'value'),
     dash.dependencies.Input('month', 'value'),
     dash.dependencies.Input('week_type', 'values')]
)
def update_vid(load_time,data_type,so,mk_in,year,drop_otdel,months,week_type):
    '''Процедура обновления таблицы с выполнением по видам страхования'''

    #Получаем данные
    main_df=get_fact_df(load_time)
    plan_df=get_plan_df(load_time)
    pp_df=get_fact_pp_df(load_time)

    #Фильтруем по отделу
    try:
        otdel=so
    except TypeError:
        otdel=' Итого'
    
    if otdel!=' Итого':
        main_df=main_df[main_df.otdel==otdel]
        plan_df=plan_df[plan_df.otdel==otdel]
        pp_df=pp_df[pp_df.otdel==otdel]

    #фильтр по месяцам
    month_list,quarter_list=get_m_q(months)
    plan_df=plan_df.astype({'quarter':'int'})
    if week_type==[]:
        main_df=main_df[main_df['month'].isin(month_list)]
        pp_df=pp_df[pp_df['month'].isin(month_list)]
        plan_df=plan_df[plan_df['quarter'].isin(quarter_list)]


    #фильтр корп
    if data_type=='Корпоратив':
        main_df=filter_corp_vidi_s_osago(main_df)
        plan_df=filter_corp_vidi_s_osago(plan_df)
        pp_df=filter_corp_vidi_s_osago(pp_df)

    #фильтр территория
    if drop_otdel=='Без Дирекции' :
        main_df=main_df[~(main_df.otdel.str.startswith('Дирекция', na=False))]
        plan_df=plan_df[~(plan_df.otdel.str.startswith('Дирекция', na=False))]
        pp_df=pp_df[~(pp_df.otdel.str.startswith('Дирекция', na=False))]
    
    

    
    #Фильтруем по мк
    mk=[]
    if isinstance(mk_in,list):
        if len(mk_in)>0 and mk_in!=[' Итого']:
            for x in mk_in:
                if x!=' Итого':
                    mk.append(x)
        elif len(mk_in)==0:
            mk=[]    
        else: 
            mk.append(' Итого')
    else:
        mk.append(mk_in)
        
    
    if mk!=[' Итого']:
        main_df=main_df[main_df.mk.isin(mk)]
        plan_df=plan_df[plan_df.mk.isin(mk)]
        pp_df=pp_df[pp_df.mk.isin(mk)]
        
    

    #определяем квартал и номер недели в квартале
    
    if week_type==['yes']:
        #номер недели
        now=datetime.datetime.now()
        week=datetime.date(now.year,now.month,now.day).isocalendar()[1]
        if week<=13:
            week_num=week
            quarter=1
        elif week>13 and week<=26:
            week_num=week-13
            quarter=2
        elif week>26 and week <=39:
            week_num=week-26
            quarter=3
        elif week>39 and week<=42:
            week_num=week-39
            quarter=4
        
    
    
    
    
    #итоговоя строка
    plan=0
    if week_type==['yes']:
        #еженедельная доля текущего квартала в зависимости от номера недели
        plan+=(week_num/13)*plan_df[plan_df['quarter']==quarter]['plan'].sum()
        #недобор за прошлые периоды. Сумма плана всех кварталов, кроме текущего - все поступления кроме текущей недели 
        plan+=(plan_df[plan_df['quarter']<quarter]['plan'].sum()-main_df[main_df['week']<week]['fact_rub'].sum())
    else:
        for q in quarter_list:
            plan+=plan_df[plan_df['quarter']==q]['plan'].sum()/3
    
    if week_type==['yes']:
        itog_row=pd.DataFrame({'vid' : [' Итого:'],'fact_rub':main_df[main_df['week']==week]['fact_rub'].sum(),'fact_sht':main_df[main_df['week']==week]['fact_sht'].sum(),'plan':plan,'fact_pp':pp_df[pp_df['week']==week]['fact_pp'].sum()})
    else:
        itog_row=pd.DataFrame({'vid' : [' Итого:'],'fact_rub':main_df['fact_rub'].sum(),'fact_sht':main_df['fact_sht'].sum(),'plan':plan,'fact_pp':pp_df['fact_pp'].sum()})
    
    
    huevi_vidi=['06. ОСАГО ФЛ','07. ОСАГО ЮЛ','90. ИСЖ','91. НСЖ']

    bez_df=main_df[~(main_df['vid'].isin(huevi_vidi))]
    bez_plan_df=plan_df[~(plan_df['vid'].isin(huevi_vidi))]
    bez_pp=pp_df[~(pp_df['vid'].isin(huevi_vidi))]


    
    bez_plan=0
    if week_type==['yes']:
        #еженедельная доля текущего квартала в зависимости от номера недели
        bez_plan+=bez_plan_df[bez_plan_df['quarter']==quarter]['plan'].sum()*week_num/13
        #недобор за прошлые периоды. Сумма плана всех кварталов, кроме текущего - все поступления кроме текущей недели 
        bez_plan+=(bez_plan_df[bez_plan_df['quarter']<quarter]['plan'].sum()-bez_df[bez_df['week']<week]['fact_rub'].sum())
    else:
        for q in quarter_list:
            bez_plan+=bez_plan_df[bez_plan_df['quarter']==q]['plan'].sum()/3
    

    if week_type==['yes']:
        bez_row=pd.DataFrame({'vid' : [' Итого без ОСАГО и проектов:'],'fact_rub':bez_df[bez_df.week==week]['fact_rub'].sum(),'fact_sht':bez_df[bez_df.week==week]['fact_sht'].sum(),'plan':bez_plan,'fact_pp':bez_pp[bez_pp.week==week]['fact_pp'].sum()})
    else:
        bez_row=pd.DataFrame({'vid' : [' Итого без ОСАГО и проектов:'],'fact_rub':bez_df['fact_rub'].sum(),'fact_sht':bez_df['fact_sht'].sum(),'plan':bez_plan,'fact_pp':bez_pp['fact_pp'].sum()})

    itog_row=itog_row.append(bez_row, ignore_index=True)
    
    #df с видами страхования для склейки
    table_df=get_vid_df(load_time)

    if week_type==[]:
        #группируем main_df  
        main_df=main_df[['vid','fact_rub','fact_sht']]
        main_df=main_df.pivot_table(index='vid',values=['fact_rub','fact_sht'], aggfunc='sum')
        main_df=pd.DataFrame(main_df.to_records())


        #вставляем факт
        table_df['fact_rub']=table_df.apply(lambda row : col_maker(row,main_df,'fact_rub'),axis=1)
        table_df['fact_sht']=table_df.apply(lambda row : col_maker(row,main_df,'fact_sht'),axis=1)
        #вставляем факт прошлого периода
        table_df['fact_pp']=table_df.apply(lambda row: col_maker(row,pp_df,'fact_pp'),axis=1)
        try:
            table_df['plan'] =table_df.apply (lambda row: plan_maker(row,plan_df,quarter_list),axis=1)
        except ValueError:
            return ''
    else:
        try:
            table_df['plan'] =table_df.apply (lambda row: week_plan_maker(row,quarter,week,week_num,plan_df,main_df),axis=1)
        except ValueError:
            return ''
        #фильтруем до текущей недели факт и факт прошлого периода
        main_df=main_df[main_df.week==week]
        pp_df=pp_df[pp_df.week==week]
        #вставляем факт
        table_df['fact_rub']=table_df.apply(lambda row : col_maker(row,main_df,'fact_rub'),axis=1)
        table_df['fact_sht']=table_df.apply(lambda row : col_maker(row,main_df,'fact_sht'),axis=1)
        #вставляем факт прошлого периода
        table_df['fact_pp']=table_df.apply(lambda row: col_maker(row,pp_df,'fact_pp'),axis=1)
      
    table_df=itog_row.append(table_df,ignore_index=True)
    








    try: 
        table_df['vp']=(table_df.fact_rub/table_df.plan)*100
        table_df['temp']=(table_df.fact_rub/table_df.fact_pp)*100
        table_df['vp']=table_df['vp'].map('{:,.2f}%'.format)
        table_df['fact_rub']=table_df['fact_rub'].map("{:,.0f}".format)
        table_df['fact_sht']=table_df['fact_sht'].map("{:,.0f}".format)
        table_df['plan']=table_df['plan'].map("{:,.0f}".format)
        table_df['fact_pp']=table_df['fact_pp'].map("{:,.0f}".format)
        
        table_df['temp']=table_df['temp'].map('{:,.2f}%'.format)

        

        
        table_df.columns=['Сборы ПП','Факт ,руб','Факт ,шт','План','Вид','Выполнение','Темп роста']
        #меняем столбцы местами
        table_df=table_df[['Вид','План','Факт ,руб','Факт ,шт','Сборы ПП','Выполнение','Темп роста']]


        
        
        
        #return   table_df.to_dict('records')
        return generate_table(table_df,40)
    except AttributeError:
        #return [{}]
        return ''





@app.callback(
     dash.dependencies.Output('vp_mk','figure'),
     [dash.dependencies.Input('stored_data', 'children'),
     dash.dependencies.Input('data_type', 'value'),
     dash.dependencies.Input('drop_so','value'),
     dash.dependencies.Input('drop_year', 'value'),
     dash.dependencies.Input('drop_otdel', 'value'),
     dash.dependencies.Input('month', 'value')]
)
def update_mk(load_time,data_type,so,year,drop_otdel,months):
    '''Процедура обновления графика
    с выполнением плана по малым каналам'''

    main_df=get_fact_df(load_time)
    plan_df=get_plan_df(load_time)
    
    #Фильтруем по отделу
    try:
        otdel=so
    except TypeError:
        otdel=' Итого'
    
    if otdel!=' Итого':
        main_df=main_df[main_df.otdel==otdel]
        plan_df=plan_df[plan_df.otdel==otdel]
        

    #фильтр по месяцам
    month_list,quarter_list=get_m_q(months)
    plan_df=plan_df.astype({'quarter':'int'})

    main_df=main_df[main_df['month'].isin(month_list)]
    plan_df=plan_df[plan_df['quarter'].isin(quarter_list)]


    #фильтр корп
    if data_type=='Корпоратив':
        main_df=filter_corp_vidi_s_osago(main_df)
        plan_df=filter_corp_vidi_s_osago(plan_df)
        
    #фильтр территория
    if drop_otdel=='Без Дирекции' :
        main_df=main_df[~(main_df.otdel.str.startswith('Дирекция', na=False))]
        plan_df=plan_df[~(plan_df.otdel.str.startswith('Дирекция', na=False))]
        
    
    #убираем трэшачок
    huevi_vidi=['06. ОСАГО ФЛ','07. ОСАГО ЮЛ','90. ИСЖ','91. НСЖ']
    main_df=main_df[~(main_df['vid'].isin(huevi_vidi))]
    plan_df=plan_df[~(plan_df['vid'].isin(huevi_vidi))]
        

   
    #добавим Итого в  наборы данных
    
    itog_row=pd.DataFrame({'otdel' : [' Итого'],
     'mk' : [' Итого']})
    main_df=main_df.append(itog_row)
    plan_df=plan_df.append(itog_row)
   
    
    #список мк с итого
    mk_spisok=plan_df.mk.unique()
    


    vp_mk=[]
    i=0
    label_txt= otdel and (otdel + ' % выполнения по каналам продаж')
    
    for mk in mk_spisok :            
            
        if mk!=' Итого':
            sorry2=main_df[(main_df['mk']==mk)]
            sorry2_plan=plan_df[(plan_df['mk']==mk)]
        else:
            sorry2=main_df
            sorry2_plan=plan_df

        plan=0
        for q in quarter_list:
            plan+=sorry2_plan[sorry2_plan['quarter']==q].ix[:,'plan'].sum()/3      
            
        if plan>0:
            vp_mk.append(int((sorry2.ix[:,'fact_rub'].sum()/(plan))*100))
        else:  vp_mk.append(0)
            
                        
        i+=1
    
    vp_df=pd.DataFrame()
    vp_df['mk']=mk_spisok
    vp_df['vp']=vp_mk
    vp_df['color']=vp_df.apply(lambda row: paint_col(row,'vp'),axis=1)  
        
        
        
        
    return { 
                        'data':[
                        {'x': vp_df.mk,
                         'y': vp_df.vp ,
                         'type' : 'bar'  ,
                         'name' : 'выполнение плана',
                         'marker' : {'color':vp_df.color}
                         }
                        #,{'x': mk_spisok, 'y': tr_mk , 'type' : 'bar' , 'name' : 'темп роста'}
                                        
                        ], 
                        'layout':{'title' :  label_txt, 'hovermode' : 'closest',"font": {
                    "size": 10
                }}
                        }




@app.callback(
     dash.dependencies.Output('vp_port','figure'),
     [dash.dependencies.Input('stored_data', 'children'),
     dash.dependencies.Input('data_type', 'value'),
     dash.dependencies.Input('drop_so','value'),
     dash.dependencies.Input('drop_mk','value'),
     dash.dependencies.Input('drop_year','value'),
     dash.dependencies.Input('drop_otdel', 'value'),
     dash.dependencies.Input('month', 'value')]
)

def update_port(load_time,data_type,so,mk_in,year,drop_otdel,months):
    '''Процедура обновления круговой диаграммы
    с составом портфеля'''
    
    main_df=get_fact_df(load_time)
        
    #Фильтруем по отделу
    try:
        otdel=so
    except TypeError:
        otdel=' Итого'
    
    if otdel!=' Итого':
        main_df=main_df[main_df.otdel==otdel]
               

    #фильтр по месяцам
    month_list,_=get_m_q(months)
  
    main_df=main_df[main_df['month'].isin(month_list)]
   

    #фильтр корп
    if data_type=='Корпоратив':
        main_df=filter_corp_vidi_s_osago(main_df)
       
    #фильтр территория
    if drop_otdel=='Без Дирекции' :
        main_df=main_df[~(main_df.otdel.str.startswith('Дирекция', na=False))]
      
    #Фильтруем по мк
    mk=[]
    if isinstance(mk_in,list):
        if len(mk_in)>0 and mk_in!=[' Итого']:
            for x in mk_in:
                if x!=' Итого':
                    mk.append(x)
        elif len(mk_in)==0:
            mk=[]    
        else: 
            mk.append(' Итого')
    else:
        mk.append(mk_in)
        
    
    if mk!=[' Итого']:
        main_df=main_df[main_df.mk.isin(mk)]
    
    title_text='состав портфеля'
  

       
    return {
                'data' : [go.Pie(labels=main_df.vid,values=main_df.fact_rub, 
                    hoverinfo='label+value+percent',
                    textinfo='none')],
                'layout' : {'title' : title_text}
            }
    






@app.callback(
     dash.dependencies.Output('weeks_dynamic','figure'),
     [dash.dependencies.Input('stored_data', 'children'),
     dash.dependencies.Input('drop_so','value'),
     dash.dependencies.Input('drop_mk','value'),
     dash.dependencies.Input('drop_otdel', 'value'),
     dash.dependencies.Input('month', 'value')
     ]
)

def update_week_dynamic(load_time,so,mk_in,drop_otdel,months):
    """ Рисуем график с поступлениями по ключевым показателям по неделям """
    main_df=get_fact_df(load_time)
    
    
    #Фильтруем по отделу
    try:
        otdel=so
    except TypeError:
        otdel=' Итого'
    
    if otdel!=' Итого':
        main_df=main_df[main_df.otdel==otdel]
        

    
    #фильтр территория
    if drop_otdel=='Без Дирекции' :
        main_df=main_df[~(main_df.otdel.str.startswith('Дирекция', na=False))]
       

    #фильтр по месяцам
    month_list,_=get_m_q(months)
  
    main_df=main_df[main_df['month'].isin(month_list)]
    
   

    #Фильтруем по мк
    mk=[]
    if isinstance(mk_in,list):
        if len(mk_in)>0 and mk_in!=[' Итого']:
            for x in mk_in:
                if x!=' Итого':
                    mk.append(x)
        elif len(mk_in)==0:
            mk=[]    
        else: 
            mk.append(' Итого')
    else:
        mk.append(mk_in)
        
    
    if mk!=[' Итого']:
        main_df=main_df[main_df.mk.isin(mk)]

    #если df пустой вернем ничего
    if main_df.empty:
        return {}  

    #проставим группу        
    main_df['группа']=main_df.apply(lambda row : group_maker(row,main_df),axis=1)

          
    #группируем данные по неделям
    df=main_df.pivot_table(index='week',columns=['группа'],values=['fact_rub'], aggfunc=sum)
    df=pd.DataFrame(df.to_records())
    

    
    #КАСКО
    try:
        k1=df["('fact_rub', 'КАСКО')"]
    except KeyError:
        nulllist=[]
        for i in df['week']:
            nulllist.append(0)
        k1=nulllist
    
    trace1=go.Scatter(
    x=df['week'],
    y=k1,
    name='КАСКО',
    mode='lines+markers',
    marker={'color':'rgba(255, 195, 0,0.82)'}
    )
    
    
    #ИФЛ
    try:
        k2=df["('fact_rub', 'ИФЛ')"]
    except KeyError:
        nulllist=[]
        for i in df['week']:
            nulllist.append(0)
        k2=nulllist
    
    
    trace2=go.Scatter(
    x=df['week'],
    y=k2,
    name='ИФЛ',
    mode='lines+markers',
    marker={'color':'rgba(71,184,16,0.82)'}
    )
    
    #остальное
    try:
        k3=df["('fact_rub', 'Остальное')"]
    except KeyError:
        nulllist=[]
        for i in df['week']:
            nulllist.append(0)
        k3=nulllist

    trace3=go.Scatter(
    x=df['week'],
    y=k3,
    name='Остальное',
    mode='lines+markers',
    marker={'color':'rgba(163, 81, 244,0.82)'}
    )
    

    #НС
    try:
        k4=df["('fact_rub', 'НС')"]
    except KeyError:
        nulllist=[]
        for i in df['week']:
            nulllist.append(0)
        k4=nulllist

    trace4=go.Scatter(
    x=df['week'],
    y=k4,
    name='НС',
    mode='lines+markers',
    marker={'color':'rgba(144,12,63,0.82)'}
    )



    data=[trace1,trace2,trace4,trace3]
    title="Динамика поступлений по неделям {}".format(so)
    return { 
                        'data':
                        data
                        ,'layout':{'title' : title,'barmode':'stack'}
                        }

