import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import pymssql
import os

import dash_table_experiments as dt
import operator
from functools import lru_cache
import datetime

from app import app,cache


def filter_corp_vidi(df):
    corp_vidi=['02','05','09','11','13','18','19','20','21','22','23','24','25','26','27','29','30','31','34','37']
    vidi=df.vid.unique()
    for vid in vidi:
        if vid[:2] not in corp_vidi:
            df=df[df.vid!=vid]
    return df

def filter_corp_vidi_s_osago(df):
    corp_vidi=['02','05','09','11','13','18','19','20','21','22','23','24','25','26','27','29','30','31','34','37','07']
    vidi=df.vid.unique()
    for vid in vidi:
        if vid[:2] not in corp_vidi:
            df=df[df.vid!=vid]
    return df

@cache.memoize()
def get_df(date):
    conn = pymssql.connect(server="10.61.0.228", user="so",password="", port=1433,charset='utf8')  # You can lookup the port number inside SQL server.
    stmt = "SELECT * FROM  svodka..analitic_app_main_data_frame"
        
    df=pd.read_sql(stmt,conn)
    #меняем пустые строки на 0
    df=df.fillna(0)
    return df
  



def layout():
    
    
    load_time=str(datetime.datetime.now())
    load_time=load_time[:15]
        
    main_df=get_df(load_time)
    table_df=main_df[['vid','fact_rub','fact_sht','plan']]
    
    return html.Div([
    
    html.Div([html.H3('Analitic App' ),dcc.RadioItems(
                        id='data_type',
                        options=[{'label': i, 'value': i} for i in ['Розница', 'Корпоратив']],
                        value='Розница'
                        #,labelStyle={'display': 'inline-block'}
                        )],style={'display':'inline-block','width':'100%','text-align': 'center'})   
                        
                        
             
    ,html.Div([
        html.Div([dcc.Dropdown(id='drop_year',options=[{'label' : i, 'value' : i } for i in main_df.year.unique()],value=main_df.year.max())],style={'width':'49%','display':'inline-block'})
        ,html.Div([dcc.Dropdown(id='drop_otdel',options=[{'label' : i, 'value' : i } for i in ['Ростов','Область','Все']],value='Все')],style={'width':'49%','display':'inline-block'})
    ]) 
    
    
    

    ,
    html.Div([ html.Div(id='stored_data',children=load_time,style={'display':'none'}),
                        dcc.Graph(id='vp_motivation')
                        ], style={'width': '100%', 'display': 'inline-block'}) 
                        ,
                        html.Div([dcc.Slider(
                        id='quarter_slider',
                        min=1,
                        max=4,
                        value=4,
                        step=None,
                        marks=[0,1,2,3,4]
                        )
                        ], style={'width': '97%', 'padding': '0px 20px 20px 20px'})
                       
                        
                       
                        ,
               html.Div([dcc.RadioItems(
                        id='quarter_type',
                        options=[{'label': i, 'value': i} for i in ['Нарастающий итог', 'Чистый квартал']],
                        value='Нарастающий итог',
                        labelStyle={'display': 'inline-block'}
                        )
                        ], style={'width': '97%', 'padding': '0px 20px 20px 20px'})
                        
                         
                    ,
                 
                        
               html.Div([
                        dcc.Graph(id='vp_mk')], style={'width': '49%', 'display': 'inline-block'}),html.Div([dcc.Graph(id='vp_port')], style={'width': '49%', 'display': 'inline-block'})
                       
                        

                        ,
                                                
               
                html.Div([html.P(id='table_title',children='Выполнение плана по видам')
                 
                 
             
              

                ,dt.DataTable(rows=table_df.to_dict('records'),

        # optional - sets the order of columns
        columns=['Вид','Выполнение','Факт ,руб','Факт ,шт','План'],

        row_selectable=False,
        filterable=False,
        sortable=False,
        editable=False,
        id='vp_vid')
      ],style={'width': '99%', 'display': 'inline-block'})
      ,html.Div([dcc.Link('Home', href='/apps/home',style={ 'text-decoration': 'underline','color':'#1F77B4'})],style={'text-align': 'center'}) ] )  
    







@app.callback(
    dash.dependencies.Output('vp_motivation', 'figure'),
    
    [dash.dependencies.Input('stored_data', 'children'),
     dash.dependencies.Input('data_type', 'value'),
     dash.dependencies.Input('drop_year', 'value'),
     dash.dependencies.Input('drop_otdel', 'value'),
     dash.dependencies.Input('quarter_slider', 'value'),
     dash.dependencies.Input('quarter_type', 'value')]
         
    )
def update_main_graph(load_time,data_type,year,drop_otdel,quarter,qtype):

   
    
    
    main_df=get_df(load_time)
    print(load_time)
    
    if data_type=='Корпоратив':
        main_df=filter_corp_vidi(main_df)
    
    #Выбор группы отделов согласно значения drop_otdel
    if drop_otdel=='Ростов' :
        main_df=main_df[(main_df.otdel.str.startswith('Дирекция', na=False)) | (main_df.otdel.str.contains('Ростов-на', na=False))]
    elif drop_otdel=='Область':
        main_df=main_df[~((main_df.otdel.str.startswith('Дирекция', na=False)) | (main_df.otdel.str.contains('Ростов-на', na=False)))]
    
        
    
    #отбираем виды для расчета выполнения мотивационного плана
    
    vidi=main_df.vid.unique()
    norm_vidi=['ТО+','ТО','Пенсионная карта','ОПС',]
    huevi_vidi=['06. ОСАГО ФЛ','07. ОСАГО ЮЛ']
    for vid in vidi:
        if vid not in norm_vidi:
            if  vid[2:4]!='. ' :
                huevi_vidi.append(vid)
    
   
    # набор с фортуной авто
    df_fortuna=main_df[main_df.vid=='36. НС Фортуна Авто']
    
    #в df_osago оставим только осаго и осаго(еа)     
    huevi_vidi2=['06. ОСАГО ФЛ','ОСАГО (ЕА)']
    for i in huevi_vidi2:
        df_osago=main_df[main_df.vid==i]
    
    
    #убираем виды не входящие в мотивацию из main_df
    for i in huevi_vidi:
        main_df=main_df[main_df.vid!=i]
    
   
    #добавим Итого в  наборы данных
    
    itog_row=pd.DataFrame({'otdel' : [' Итого'],
     'mk' : [' Итого']})
    main_df=main_df.append(itog_row)
    df_osago=df_osago.append(itog_row)
    df_fortuna=df_fortuna.append(itog_row)
    
    #список отделов с итого
    
    otdel_spisok=main_df.otdel.unique()    
    
    
    
    
    vp_otdel=[]   
    i=0
    
    #фильтруем данные согласно выбранного режима
    if qtype=='Нарастающий итог':
        
        for a in otdel_spisok :
            if a==' Итого':
                sorry=main_df[ (main_df['year']==year) & (main_df['quarter']<=quarter)]
                sorry_osago=df_osago[ (df_osago['year']==year) & (df_osago['quarter']<=quarter)]
                sorry_fortuna=df_fortuna[ (df_fortuna['year']==year) & (df_fortuna['quarter']<=quarter)]
            else:
                sorry=main_df[(main_df['otdel']==a) & (main_df['year']==year) & (main_df['quarter']<=quarter)]
                sorry_osago=df_osago[(df_osago['otdel']==a) & (df_osago['year']==year) & (df_osago['quarter']<=quarter)]
                sorry_fortuna=df_fortuna[(df_fortuna['otdel']==a) & (df_fortuna['year']==year) & (df_fortuna['quarter']<=quarter)]
            if sorry.ix[:,'plan'].sum()>0:
                vp_otdel.append(int((sorry.ix[:,'fact_rub'].sum()/(sorry.ix[:,'plan'].sum()-sorry_fortuna.ix[:,'plan'].sum()+1270.913*(sorry_osago.ix[:,'fact_sht'].sum())))*100))
            else:  vp_otdel.append(0)
            i+=1
            
    else:
        
        for a in otdel_spisok :
            if a==' Итого' :
                sorry=main_df[ (main_df['year']==year) & (main_df['quarter']==quarter)]
                sorry_osago=df_osago[ (df_osago['year']==year) & (df_osago['quarter']==quarter)]
                sorry_fortuna=df_fortuna[ (df_fortuna['year']==year) & (df_fortuna['quarter']==quarter)]
            else:
                sorry=main_df[(main_df['otdel']==a) & (main_df['year']==year) & (main_df['quarter']==quarter)]
                sorry_osago=df_osago[(df_osago['otdel']==a) & (df_osago['year']==year) & (df_osago['quarter']==quarter)]
                sorry_fortuna=df_fortuna[(df_fortuna['otdel']==a) & (df_fortuna['year']==year) & (df_fortuna['quarter']==quarter)]
            if sorry.ix[:,'plan'].sum()>0:
                vp_otdel.append(int((sorry.ix[:,'fact_rub'].sum()/(sorry.ix[:,'plan'].sum()-sorry_fortuna.ix[:,'plan'].sum()+1270.913*(sorry_osago.ix[:,'fact_sht'].sum())))*100))
            else:  vp_otdel.append(0)
            i+=1
            
    vp_data= dict(zip(otdel_spisok, vp_otdel))
    
        
    
    #возвращаем график
    return { 
                        'data':[
                        {'x': sorted(vp_data, key=vp_data.get), 'y': sorted(vp_data.values()) , 'type' : 'bar' ,'name' : 'выполнение плана'}]
                        ,'layout':{'title' : '% выполнения мотивационного плана','hovermode' : 'closest'}
                        }


############norm polet


@app.callback(
     dash.dependencies.Output('vp_vid','rows'),
     [dash.dependencies.Input('stored_data', 'children'),
     dash.dependencies.Input('data_type', 'value'),
     dash.dependencies.Input('vp_motivation','clickData'),
     dash.dependencies.Input('vp_mk','clickData'),
     dash.dependencies.Input('drop_year', 'value'),
     dash.dependencies.Input('drop_otdel', 'value'),
     dash.dependencies.Input('quarter_slider', 'value'),
     dash.dependencies.Input('quarter_type', 'value')]0 	2018 	1 	АГЕНТ1 	БЕРЕЗУЦКАЯ Т Т 	руб 	3480.0 	15. Квартиры 	36108500 	Агентский 	None
1 	2018 	1 	АГЕНТ1 	БЕРЕЗУЦКАЯ Т Т 	шт 	4.0 	15. Квартиры 	36108500 	Агентский 	None
2 	2018 	1 	АГЕНТ1 	МАЛЫШЕВА О Н 	руб 	650.0 	14. Строения 	36108500 	Агентский 	None
3 	2018 	1 	АГЕНТ1 	МАЛЫШЕВА О Н 	шт 	1.0 	14. Строения 	36108500 	Агентский 	None
4 	2018 	1 	АГЕНТ1 	МАЛЫШЕВА О Н 	руб 	3250.0 	15. Квартиры 	36108500 	Агентский 	None
5 	2018 	1 	АГЕНТ1 	МАЛЫШЕВА О Н 	шт 	5.0 	15. Квартиры 	36108500 	Агентский 	None
12 	2018 	1 	АГЕНТ1 	ПОТОЦКАЯ Н А 	руб 	2590.0 	14. Строения 	36108500 	Агентский 	None
13 	2018 	1 	АГЕНТ1 	ПОТОЦКАЯ Н А 	шт 	1.0 	14. Строения 	36108500 	Агентский 	None
     )
def update_vid(load_time,data_type,some,mk_in,year,drop_otdel,quarter,qtype):
   
     
    #Получаем данные
    main_df=get_df(load_time)
    
    if data_type=='Корпоратив':
        main_df=filter_corp_vidi_s_osago(main_df)
    
    #Выбор группы отделов согласно значения drop_otdel
    if drop_otdel=='Ростов' :
        main_df=main_df[(main_df.otdel.str.startswith('Дирекция', na=False)) | (main_df.otdel.str.contains('Ростов-на', na=False))]
    elif drop_otdel=='Область':
        main_df=main_df[~((main_df.otdel.str.startswith('Дирекция', na=False)) | (main_df.otdel.str.contains('Ростов-на', na=False)))]
    
    
    #Фильтруем по отделу
    try:
        otdel=some['points'][0]['x']
    except TypeError:
        otdel=' Итого'
    
    if otdel!=' Итого':
        main_df=main_df[main_df.otdel==otdel]
    #Фильтруем по году
    main_df=main_df[main_df.year==year]
    #Фильтруем по кварталам
    if qtype!='Нарастающий итог':
        main_df=main_df[main_df.quarter==quarter]
    else:
        main_df=main_df[main_df.quarter<=quarter]
    
    #Фильтруем по мк
    try:
        mk=mk_in['points'][0]['x']
    except TypeError:
        mk=' Итого'    
    
    if mk!=' Итого':
        main_df=main_df[main_df.mk==mk]
        
    table_df=main_df[['vid','fact_rub','fact_sht','plan']]
    table_df=table_df.pivot_table(index='vid',values=['fact_rub','fact_sht','plan'], aggfunc='sum')
    table_df=pd.DataFrame(table_df.to_records())
    try: 
        table_df['vp']=(table_df.fact_rub/table_df.plan)*100
        table_df['vp']=table_df['vp'].map('{:,.2f}%'.format)
        table_df['fact_rub']=table_df['fact_rub'].map("{:,.0f}".format)
        table_df['fact_sht']=table_df['fact_sht'].map("{:,.0f}".format)
        table_df['plan']=table_df['plan'].map("{:,.0f}".format)
        table_df.columns=['Вид','Факт ,руб','Факт ,шт','План','Выполнение']
        return   table_df.to_dict('records')
    except AttributeError:
        return [{}]



@app.callback(
     dash.dependencies.Output('table_title','children'),
     [dash.dependencies.Input('vp_motivation','clickData'),
      dash.dependencies.Input('vp_mk','clickData')]
     )

def update_table_title(some,mk_in):
    try:
        otdel=some['points'][0]['x']
    except TypeError:
        otdel=' Все отделы'
        
    try:
        mk=mk_in['points'][0]['x']
    except TypeError:
        mk=' Все каналы'
        
    if mk==' Итого':
        mk=' Все каналы'
        
    if otdel==' Итого':
        otdel='Все отделы'
        
    title='Выполнение по видам отдел: ' + otdel + ' ,канал: ' + mk
    return title
    




@app.callback(
     dash.dependencies.Output('vp_mk','figure'),
     [dash.dependencies.Input('stored_data', 'children'),
     dash.dependencies.Input('data_type', 'value'),
     dash.dependencies.Input('vp_motivation','clickData'),
     dash.dependencies.Input('drop_year', 'value'),
     dash.dependencies.Input('drop_otdel', 'value'),
     dash.dependencies.Input('quarter_slider', 'value'),
     dash.dependencies.Input('quarter_type', 'value')]
     )
def update_mk(load_time,data_type,some,year,drop_otdel,quarter,qtype):
   
     
    
    main_df=get_df(load_time)
    
    if data_type=='Корпоратив':
        main_df=filter_corp_vidi(main_df)
    
    #Выбор группы отделов согласно значения drop_otdel
    if drop_otdel=='Ростов' :
        main_df=main_df[(main_df.otdel.str.startswith('Дирекция', na=False)) | (main_df.otdel.str.contains('Ростов-на', na=False))]
    elif drop_otdel=='Область':
        main_df=main_df[~((main_df.otdel.str.startswith('Дирекция', na=False)) | (main_df.otdel.str.contains('Ростов-на', na=False)))]
    
    #отбираем виды для расчета выполнения мотивационного плана
    
    vidi=main_df.vid.unique()
    norm_vidi=['ТО+','ТО','Пенсионная карта','ОПС',]
    huevi_vidi=['06. ОСАГО ФЛ','07. ОСАГО ЮЛ']
    for vid in vidi:
        if vid not in norm_vidi:
            if  vid[2:4]!='. ' :
                huevi_vidi.append(vid)
    
   
    # набор с фортуной авто
    df_fortuna=main_df[main_df.vid=='36. НС Фортуна Авто']
    
    #в df_osago оставим только осаго и осаго(еа)     
    huevi_vidi2=['06. ОСАГО ФЛ','ОСАГО (ЕА)']
    for i in huevi_vidi2:
        df_osago=main_df[main_df.vid==i]
    
    
    #убираем виды не входящие в мотивацию из main_df
    for i in huevi_vidi:
        main_df=main_df[main_df.vid!=i]
    
   
    #добавим Итого в  наборы данных
    
    itog_row=pd.DataFrame({'otdel' : [' Итого'],
     'mk' : [' Итого']})
    main_df=main_df.append(itog_row)
    df_osago=df_osago.append(itog_row)
    df_fortuna=df_fortuna.append(itog_row)
    
    #список отделов с итого
    
       
    mk_spisok=main_df.mk.unique()
    
    try:
        otdel=some['points'][0]['x']
    except TypeError:
        otdel=' Итого'
   
    
    
    vp_mk=[]
    tr_mk=[]
    i=0
    sorry=main_df[(main_df['year']==year)]
    sorry_osago=df_osago[(df_osago['year']==year)]
    sorry_fortuna=df_fortuna[(df_fortuna['year']==year)]
    if qtype=='Нарастающий итог':
        label_txt= otdel + ' % выполнения по каналам продаж' 
        if otdel==' Итого':
            sorry=sorry[sorry['quarter']<=quarter]
            sorry_osago=sorry_osago[sorry_osago['quarter']<=quarter]
            sorry_fortuna=sorry_fortuna[sorry_fortuna['quarter']<=quarter]
        else :
            sorry=sorry[(sorry['otdel']==otdel)   & (sorry['quarter']<=quarter)]
            sorry_osago=sorry_osago[(sorry_osago['otdel']==otdel)   & (sorry_osago['quarter']<=quarter)]
            sorry_fortuna=sorry_fortuna[(sorry_fortuna['otdel']==otdel)   & (sorry_fortuna['quarter']<=quarter)]
        for mk in mk_spisok :            
            
            if mk!=' Итого':
                sorry2=sorry[(sorry['mk']==mk)]
                sorry2_osago=sorry_osago[(sorry_osago['mk']==mk)]
                sorry2_fortuna=sorry_fortuna[(sorry_fortuna['mk']==mk)]
            else:
                sorry2=sorry
                sorry2_osago=sorry_osago
                sorry2_fortuna=sorry_fortuna
                
                
            
            
            if sorry2.ix[:,'plan'].sum()>0:
                vp_mk.append(int((sorry2.ix[:,'fact_rub'].sum()/(sorry2.ix[:,'plan'].sum()-sorry2_fortuna.ix[:,'plan'].sum()+1270.913*(sorry2_osago.ix[:,'fact_sht'].sum())))*100))
                
            else:  vp_mk.append(0)
            
            if sorry2.ix[:,'fact_pp'].sum()>0:
                tr_mk.append(int((sorry2.ix[:,'fact_rub'].sum()/sorry2.ix[:,'fact_pp'].sum())*100)-100)
            else: tr_mk.append(0)
            
            i+=1
    else:
        
        label_txt= otdel + ' % выполнения по каналам продаж '
        if otdel==' Итого':
            sorry=sorry[ (sorry['quarter']==quarter)]
            sorry_osago=sorry_osago[sorry_osago['quarter']==quarter]
            sorry_fortuna=sorry_fortuna[sorry_fortuna['quarter']==quarter]
        else :
            sorry=sorry[(sorry['otdel']==otdel) & (sorry['quarter']==quarter) ]
            sorry_osago=sorry_osago[(sorry_osago['otdel']==otdel)   & (sorry_osago['quarter']==quarter)]
            sorry_fortuna=sorry_fortuna[(sorry_fortuna['otdel']==otdel)   & (sorry_fortuna['quarter']==quarter)]
        
        for mk in mk_spisok :
            
            
            if mk!=' Итого':
                sorry2=sorry[(sorry['mk']==mk)]
                sorry2_osago=sorry_osago[(sorry_osago['mk']==mk)]
                sorry2_fortuna=sorry_fortuna[(sorry_fortuna['mk']==mk)]
            else:
                sorry2=sorry
            
            if sorry2.ix[:,'plan'].sum()>0:
                vp_mk.append(int((sorry2.ix[:,'fact_rub'].sum()/(sorry2.ix[:,'plan'].sum()-sorry2_fortuna.ix[:,'plan'].sum()+1270.913*(sorry2_osago.ix[:,'fact_sht'].sum())))*100))
                
            else:  vp_mk.append(0)
            
            if sorry2.ix[:,'fact_pp'].sum()>0:
                tr_mk.append(int((sorry2.ix[:,'fact_rub'].sum()/sorry2.ix[:,'fact_pp'].sum())*100)-100)
            else: tr_mk.append(0)
                
                
            i+=1
        
        
        
        
        
    return { 
                        'data':[
                        {'x': mk_spisok, 'y': vp_mk , 'type' : 'bar'  , 'name' : 'выполнение плана'}
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
     dash.dependencies.Input('vp_motivation','clickData'),
     dash.dependencies.Input('vp_mk','clickData'),
     dash.dependencies.Input('drop_year','value'),
     dash.dependencies.Input('drop_otdel', 'value'),
     dash.dependencies.Input('quarter_slider', 'value'),
     dash.dependencies.Input('quarter_type', 'value')]
    )

def update_port(load_time,data_type,some,mk_in,year,drop_otdel,quarter,qtype):
   
  
     
    
    main_df=get_df(load_time)
    
    if data_type=='Корпоратив':
        main_df=filter_corp_vidi_s_osago(main_df)
    
    #Выбор группы отделов согласно значения drop_otdel
    if drop_otdel=='Ростов' :
        main_df=main_df[(main_df.otdel.str.startswith('Дирекция', na=False)) | (main_df.otdel.str.contains('Ростов-на', na=False))]
    elif drop_otdel=='Область':
        main_df=main_df[~((main_df.otdel.str.startswith('Дирекция', na=False)) | (main_df.otdel.str.contains('Ростов-на', na=False)))]
    
    
    try:
        otdel=some['points'][0]['x']
    except TypeError:
        otdel=' Итого'
    
    try:
        mk=mk_in['points'][0]['x']
    except TypeError:
        mk=' Итого'

    
    
    
    title_text='состав портфеля канал ' + mk  
    if otdel!=' Итого':
        sorry=main_df[main_df.otdel==otdel]
    else:
        sorry=main_df
    
    
    
    #виды список
    vid_spisok=sorry.vid.unique()
    
    
    vidi=[]
    sbori=[]
    
    if qtype=='Нарастающий итог':
        sorry=sorry[ (sorry.year==year) & (sorry.quarter<=quarter)]
    else:
        sorry=sorry[ (sorry.year==year) & (sorry.quarter==quarter)]
        
    if mk!=' Итого':
            sorry=sorry[sorry.mk==mk]
            
    huevi_vidi=['Депозит (размещение)','Депозит (пополнение)','Депозит (закрытие)']
    
    for vid in vid_spisok:
        if str(vid) not in huevi_vidi:
            sorry2=sorry[sorry.vid==vid]
            vidi.append(str(vid))
            sbori.append(sorry2.ix[:,'fact_rub'].sum())
        
        
            
    
    sbori_deposit=sorry[sorry.vid=='Депозит (размещение)'].ix[:,'fact_rub'].sum()+sorry[sorry.vid=='Депозит (пополнение)'].ix[:,'fact_rub'].sum()-sorry[sorry.vid=='Депозит (закрытие)'].ix[:,'fact_rub'].sum()
    
    
    sbori2=[]
    vid_spisok2=[]
    if sbori_deposit>0:
        sbori2.append(sbori_deposit)
        vid_spisok2.append('Депозит (прирост)')
    
    for i in range(0,len(sbori)):
        if sbori[i]>0:
            sbori2.append(sbori[i])
            vid_spisok2.append(vidi[i])
       
    return {
                'data' : [go.Pie(labels=vid_spisok2,values=sbori2, 
                
                hoverinfo='label+value+percent',
                textinfo='none' )], 'layout' : {'title' : title_text}
                
                }
    
