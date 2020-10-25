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

departments_dict={
'36107080':'АГЗападное',
'36108020':'Азов','36108030':'Аксай','36108040':'Багаевская','36108050':'Боковская',
'36108060':'Казанская','36108070':'Веселый','36108080':'Романовская',
'36107090':'АГПервомайское','36108090':'Дубовское',
'36108100':'Егорлыкская','36108110':'Зерноград','36108120':'Зимовники',
'36108130':'Глубокий','36108140':'Кашары','36108150':'Константиновск',
'36108160':'Большая Мартыновка','36108170':'Матвеев Курган',
'36108180':'Милютинская',
'36108190':'Морозовск',
'36108200':'Чалтырь',
'36108210':'Покровское',
'36108220':'Обливская',
'36108230':'Каменоломни',
'36108240':'Орловский',
'36108250':'Песчанокопское',
'36108260':'Пролетарск',
'36108270':'Ремонтное',
'36108280':'Родионово-Несветайская',
'36108290':'СО Пушкинский',
'36108300':'Семикаракорск',
'36108310':'Тарасовский',
'36108320':'Тацинская',
'36108330':'Усть-Донецкий',
'36108340':'Целина',
'36108350':'Цимлянск',
'36108360':'Чертково',
'36108370':'Вешенская',
'36108390':'Батайск',
'36108400':'Белая Калитва',
'36108410':'Волгодонск',
'36108420':'Гуково',
'36108430':'Донецк',
'36108440':'Зверево',
'36108450':'Каменск-Шахтинский',
'36108460':'Красный Сулин',
'36108470':'Миллерово',
'36108480':'Новошахтинск',
'36108490':'Сальск',
'36108500':'Новочеркасск',
'36108520':'Таганрог',
'36108540':'Шахты',
'36108560':'Ворошиловский',
'36108590':'Октябрьский',
'36108600':'СО Первомайский',
'36108610':'СО Пролетарский',
'36150010':'Дирекция'}
    
       
def rounder(row):
    a=round(row['вп'],2)
    return a
            
def opr_last_year(row):
    load_time=str(datetime.datetime.now())
    load_time=load_time[:15]
    current_year=int(load_time[:4])
    if row['Спр | Вид | Вид с ФЛ-ЮЛ']=='27. ОПР':
        if row['Спр | Время | Год']!=current_year:
            result_col='Прошлый год факт'        
            new_value=28*row[result_col]/100
            return new_value
    else:
        return row['Прошлый год факт']
    
def opr_current_year(row):
    load_time=str(datetime.datetime.now())
    load_time=load_time[:15]
    current_year=int(load_time[:4])
    if row['Спр | Вид | Вид с ФЛ-ЮЛ']=='27. ОПР':
        if row['Спр | Время | Год']==current_year:
            result_col='Текущий год факт'
            new_value=28*row[result_col]/100
            return new_value
    else:
        return row['Текущий год факт']

def cbd_rename_stream(row):
    result=departments_dict.get(str(row['скк']))
    return result

def cbd_rename_quantity(row):
    result=departments_dict.get(str(row['Код СКК']))
    return result

def cbd_rename_value(row):
    result=departments_dict.get(str(row['я. Код СКК']))
    return result


@cache.memoize(timeout=60*10)
def get_stream_df(date):
    df=pd.read_excel('iron_stream.xls',encoding='utf-8')
    #оставляем 28% от ОПР
    df['со']=df.apply(lambda row: cbd_rename_stream(row),axis=1)
    #меняем пустые строки на 0
    df=df.fillna(0)
    return df

@cache.memoize(timeout=60*10)
def get_value_df(date):

    df=pd.read_excel('cbd_value.xls',encoding='utf-8')
    
    #оставляем 28% от ОПР
    df['Текущий год факт']=df.apply(lambda row : opr_current_year(row),axis=1)
    df['Прошлый год факт']=df.apply(lambda row : opr_last_year(row),axis=1)
    df['Спр | Регион | Подразделение']=df.apply(lambda row: cbd_rename_value(row),axis=1)
    #меняем пустые строки на 0
    df=df.fillna(0)
    return df
  
@cache.memoize(timeout=60*10)
def get_quantity_df(date):
            
    df=pd.read_excel('cbd_quantity.xls',encoding='utf-8')
    #меняем пустые строки на 0
    df=df.fillna(0)
    #оставляем только ОСАГО ФЛ
    df=df[df['Спр | Вид | Вид с ФЛ-ЮЛ']=='06. ОСАГО ФЛ']
    df['Спр | Регион | Подразделение']=df.apply(lambda row: cbd_rename_quantity(row),axis=1)
    return df
    
    
@cache.memoize(timeout=60*10)
def get_plan_df(date):
    conn = pymssql.connect(server="10.61.0.228", user="so",password="", port=1433,charset='utf8')  # You can lookup the port number inside SQL server.
    stmt = "SELECT * FROM  svodka..cbd_plan_df"
        
    df=pd.read_sql(stmt,conn)
    #меняем пустые строки на 0
    
    df[['год','план','квартал']] = df[['год','план','квартал']].apply(pd.to_numeric)
    df=df.fillna(0)
    return df


def layout():
    
    
    load_time=str(datetime.datetime.now())
    load_time=load_time[:15]
    df=get_value_df(load_time)
    dff=df[df['Текущий год факт']>0]
    dep_list=[]
    for key in departments_dict.keys():    
        dep_list.append(departments_dict.get(key))
    dep_list.append('Все')
    
    
    years=df['Спр | Время | Год'].unique().tolist()
    
    big_channels=['Розница','Корпоратив','Партнеры']
    insurance_types=['КАСКО','ИФЛ','Железный поток']
    insurance_types.append('Мотивационный план')
    
    return html.Div([
        #control panel
            html.Div(className='col-lg-2 left-pan',children=[
                html.Br(),
                html.Br(),
                html.Br(),
                html.Br(),
                html.Br(),

                html.Div(className='page-header',children=[
                    html.H5('Канал продаж :'),

                    dcc.Dropdown(id='cbd_big_channel',options=[{'label' : i, 'value' : i } for i in big_channels],value='Розница')
                ]),

                html.Div(className='page-header',children=[
                    html.H5('Год :'),
                    dcc.Dropdown(id='cbd_year',options=[{'label' : i, 'value' : i } for i in years],value=2018)
                ]),


                #load time as key value for redis
                html.Div(id='cbd_stored_data',children=load_time,style={'display':'none'}),
                html.Div(className='page-header',children=[
                    html.H5('Квартал :'),
                    dcc.RadioItems(
                        id='cbd_quarter_type',
                        options=[{'label': i, 'value': i} for i in ['Нарастающий итог', 'Чистый квартал']],
                        value='Нарастающий итог',
                        labelStyle={'display': 'block'}
                        ),
                    dcc.Slider(
                        id='cbd_quarter_slider',
                        min=1,
                        max=4,
                        value=4,
                        step=None,
                        marks=[0,1,2,3,4]
                        ),
                    html.Br()
                    
                ]),
                html.Div(className='page-header',children=[
                    html.H5('Показатель :'),
                    dcc.Dropdown(id='cbd_insurance_types',options=[{'label' : i, 'value' : i } for i in  insurance_types],value='Мотивационный план')
                ]),

            ])
        ,
        #bs row with page title
        html.Div(className='row',children=[
            html.Div(className='col-lg-2'),
            html.Div(className='col-lg-10',children=html.H4(className='page-header center-text',children='Выполнение ключевых показателей по данным ЦБД'))
            ]),
        #bs row with content
        html.Div(className='row',children=[
            
            #graphs
            html.Div(className='col-lg-2'),
            html.Div(className='col-lg-10',children=[
                html.Div(id='graph_table_keeper')
            ])
            
        ]) 
    ])

    
    


@app.callback(
dash.dependencies.Output('graph_table_keeper','children'),
[dash.dependencies.Input('cbd_stored_data','children'),
dash.dependencies.Input('cbd_insurance_types','value'),
dash.dependencies.Input('cbd_year','value'),
dash.dependencies.Input('cbd_big_channel','value'),
dash.dependencies.Input('cbd_quarter_slider','value'),
dash.dependencies.Input('cbd_quarter_type','value')]
)

def update_cbd_main_graph(stored_data,calculation_type,year,big_channel,quarter,quarter_type):
    
    #загружаем данные
    if calculation_type !='Железный поток':
        value_df=get_value_df(stored_data)
        plan_df=get_plan_df(stored_data)
        quantity_df=get_quantity_df(stored_data)
       
        current_year=int(stored_data[:4])
    
        #убираем трэшак из плана
        plan_df=plan_df[plan_df['план']>1]
   
        #отбираем только факт
        value_df=value_df[(value_df['Текущий год факт']!=0) | (value_df['Прошлый год факт']!=0) ]
    
        title='выполнения мотивационного плана Филиала {:,.2f}% Сборы {:,.0f} План {:,.0f} '
        #логика расчета
        if calculation_type=='КАСКО':
            title='выполнение  Филиалом плана по КАСКО {:,.2f}% Сборы {:,.0f} План {:,.0f} '
            norm=['08. КАСКО ФЛ','09. КАСКО ЮЛ']
            value_df=value_df[(value_df['Спр | Вид | Вид с ФЛ-ЮЛ']=='08. КАСКО ФЛ') | (value_df['Спр | Вид | Вид с ФЛ-ЮЛ']=='09. КАСКО ЮЛ')]
            quantity_df=quantity_df[(quantity_df['Спр | Вид | Вид с ФЛ-ЮЛ']=='08. КАСКО ФЛ') | (quantity_df['Спр | Вид | Вид с ФЛ-ЮЛ']=='09. КАСКО ЮЛ')]
            plan_df=plan_df[(plan_df['вид страхования']=='08. КАСКО ФЛ') | (plan_df['вид страхования']=='09. КАСКО ЮЛ')]
        elif calculation_type=='ИФЛ':
            title='выполнение  Филиалом плана по ИФЛ {:,.2f}% Сборы {:,.0f} План {:,.0f} '
            norm=['14. Строения','15. Квартиры']
            value_df=value_df[(value_df['Спр | Вид | Вид с ФЛ-ЮЛ']=='14. Строения') | (value_df['Спр | Вид | Вид с ФЛ-ЮЛ']=='15. Квартиры')]
            quantity_df=quantity_df[(quantity_df['Спр | Вид | Вид с ФЛ-ЮЛ']=='14. Строения') | (quantity_df['Спр | Вид | Вид с ФЛ-ЮЛ']=='15. Квартиры')]
            plan_df=plan_df[(plan_df['вид страхования']=='14. Строения') | (plan_df['вид страхования']=='15. Квартиры')]
    
    
        #фильтруем по году
        quantity_df=quantity_df[quantity_df['Год']==year]
        plan_df=plan_df[plan_df['год']==year]
        if year==current_year:
            result_col='Текущий год факт'
        else:
            result_col='Прошлый год факт'
    
    
    
        #фильтруем по большому каналу
        if big_channel=='Корпоратив':
            quantity_df=quantity_df[quantity_df['Спр | Канал | БК | Корпоратив']=='2. Корпоратив']
            value_df=value_df[value_df['Спр | Канал | БК | Корпоратив']=='2. Корпоратив']
            plan_df=plan_df[plan_df['Канал продаж']=='Корпоративный']
        elif big_channel=='Партнеры':
            quantity_df=quantity_df[quantity_df['Спр | Канал | БК | Партнеры']=='3. Партнеры']
            value_df=value_df[value_df['Спр | Канал | БК | Партнеры']=='3. Партнеры']
            plan_df=plan_df[plan_df['Канал продаж']=='Партнерский']
        else:
            plan_df=plan_df[plan_df['Канал продаж']=='Розничный']
        
        
        #фильтруем по кварталу с учетом режима НИ или ЧК
        if quarter_type=='Чистый квартал':
            quantity_df=quantity_df[quantity_df['Спр | Время | Квартал | Номер квартала']==quarter]
            value_df=value_df[value_df['Спр | Время | Квартал | Номер квартала']==quarter]
            plan_df=plan_df[plan_df['квартал']==quarter]
        else:
            quantity_df=quantity_df[quantity_df['Спр | Время | Квартал | Номер квартала']<=quarter]
            value_df=value_df[value_df['Спр | Время | Квартал | Номер квартала']<=quarter]
            plan_df=plan_df[plan_df['квартал']<=quarter]
 
       
   
         
        #Все виды из плана
        plan_insurance_types=plan_df['вид страхования'].unique().tolist()
    
        #немотивационное говно вычитаемое из плана
        plan_retarded_insurance_types=['06. ОСАГО ФЛ','07. ОСАГО ЮЛ','36. НС Фортуна Авто']
        for vid in  plan_insurance_types:
            if vid!='Пенсионная карта':
                if vid!='ОПС':
                    if  vid[2:4]!='. ' :
                        plan_retarded_insurance_types.append(vid)
    
    
        #фильтруем план по видам
        for insurance_type in plan_retarded_insurance_types:
            plan_df=plan_df[plan_df['вид страхования']!=insurance_type]
    
        #немотивационное говно вычитаемое из факта
        income_retarded_insurance_types=['06. ОСАГО ФЛ','07. ОСАГО ЮЛ']
    
        #фильтруем факт по видам
        for retarded_insurance_type in income_retarded_insurance_types:
            value_df=value_df[value_df['Спр | Вид | Вид с ФЛ-ЮЛ']!=retarded_insurance_type]
    
   
    
        vp=[]
        value=[]
        plan=[]
        departments=[]
    
        def osago_penalty(df):
            p1=df[df['Спр | Время | Квартал | Номер квартала']==1]
            p2=df[df['Спр | Время | Квартал | Номер квартала']==2]
            p3=df[df['Спр | Время | Квартал | Номер квартала']==3]
            p4=df[df['Спр | Время | Квартал | Номер квартала']==4]
            k1=1610.43
            k2=1925.87
            k3=370.12
            k4=364.33
            total= k1*p1['Количество заключенных договоров'].sum()+k2*p2['Количество заключенных договоров'].sum()
            total+=k3*p3['Количество заключенных договоров'].sum()+k4*p4['Количество заключенных договоров'].sum()
            if calculation_type!='Мотивационный план':
                return 0
            else:
                return total
    
    
        #выполнение плана итого по области
        if (plan_df['план'].sum()+osago_penalty(quantity_df))>0:
            vp_total=100*1000*value_df[result_col].sum()/(plan_df['план'].sum()+osago_penalty(quantity_df))
        else:
            vp_total=0
        value_total=value_df[result_col].sum()
        plan_total=(plan_df['план'].sum()+osago_penalty(quantity_df))/(1000)
    
   
        #расчет плана дирекции
        rozn_plan=plan_df[plan_df['скк']=='36150010р']
        corp_plan=plan_df[plan_df['скк']=='36150010к']
        partner_plan=plan_df[plan_df['скк']=='36150010п']
       
        direction_plan=rozn_plan['план'].sum()+corp_plan['план'].sum()+partner_plan['план'].sum()+osago_penalty(quantity_df[quantity_df['Код СКК']==36150010])
    
    
        #расчет выполнения плана по отделам
      
        for skk_code, department in departments_dict.items():
            department_value=value_df[value_df['Спр | Регион | Подразделение']==department]
            department_osago=quantity_df[quantity_df['Спр | Регион | Подразделение']==department]
        
       
        
            #ищем соответствующий план
            department_plan=plan_df[plan_df['скк']==skk_code]
        
            if skk_code=='36150010':
                if direction_plan>0:
                    a=100*1000*department_value[result_col].sum()/direction_plan
                    vp.append(round(a,2))
                else:
                    vp.append(0)
                departments.append(department)
                a=department_value[result_col].sum()
                value.append(round(a,2))
                a=direction_plan/(1000)
                plan.append(round(a,2))
            
            
            if department_plan['план'].sum()>0:
                a=(100*1000*department_value[result_col].sum())/(department_plan['план'].sum()+osago_penalty(department_osago))
                vp.append(round(a,2))
                #уберем СКК из названия
                departments.append(department)
                a=department_value[result_col].sum()
                value.append(round(a,2))
                a=(department_plan['план'].sum()+osago_penalty(department_osago))/(1000)
                plan.append(round(a,2))
            
       
    

       
        table_data=pd.DataFrame()
        table_data['Отдел']=departments
        table_data['План']=plan
        table_data['Факт']=value
        table_data['ВП']=vp
    
    
        table_data.columns=['Отдел','План','Факт','ВП']
        '''table_data['ВП']=table_data['ВП'].map('{:,.2f}%'.format)
        table_data['Факт']=table_data['Факт'].map("{:,.0f}".format)
        table_data['План']=table_data['План'].map("{:,.0f}".format)'''
    
   
        return html.Div([dcc.Graph(id='rating_graph')
            ,dt.DataTable(id='table',rows=table_data.to_dict('records'),
            # optional - sets the order of columns
            columns=['Отдел','План','Факт','ВП'],
            row_selectable=False,
            filterable=True,
            sortable=True,
            editable=False,
        
            )])
    else:
        stream_df=get_stream_df(stored_data)
        stream_df=stream_df.sort_values(by=['вп'])
        stream_df=stream_df[stream_df['год']==year]
        
        if quarter_type=='Нарастающий итог':
            stream_df=stream_df[stream_df['квартал']<=quarter]
        else:
            stream_df=stream_df[stream_df['квартал']==quarter]
        
        graph_df=stream_df[['со','факт','план']]
        graph_df=graph_df.pivot_table(index='со',values=['факт','план'], aggfunc=sum)
        graph_df=pd.DataFrame(graph_df.to_records())
        graph_df['вп']=(100*graph_df['факт']/graph_df['план'])
        
        
        graph_df['вп']=graph_df.apply(lambda row: rounder(row),axis=1)
       
        
        #graph_df.columns=
        graph_df.columns=['Отдел','План','Факт','ВП']
        title='выполнение плана Филиала по железному потоку {:,.2f}% Факт {:,.0f} План {:,.0f} '
        return html.Div([dcc.Graph(id='rating_graph')
            ,dt.DataTable(id='table',rows=graph_df.to_dict('records'),
            # optional - sets the order of columns
            columns=['Отдел','План','Факт','ВП'],
            row_selectable=False,
            filterable=True,
            sortable=True,
            editable=False,
        
            )])


@app.callback(dash.dependencies.Output('rating_graph','figure'),
[dash.dependencies.Input('table','rows'),
dash.dependencies.Input('cbd_insurance_types','value')])

def update_rating_graph(rows,calculation_type):
    df=pd.DataFrame(rows)
    if calculation_type=='ИСЖ':
        title='выполнение  Филиалом плана по ИСЖ {:,.2f}% Сборы {:,.0f} План {:,.0f} '
           
    elif calculation_type=='Жизнь':
        title='выполнение  Филиалом плана по Жизни {:,.2f}% Сборы {:,.0f} План {:,.0f} '
            
    elif calculation_type=='Марс':
        title='выполнение  Филиалом плана по МАРСУ {:,.2f}% Сборы {:,.0f} План {:,.0f} '
            
    elif calculation_type=='КАСКО':
        title='выполнение  Филиалом плана по КАСКО {:,.2f}% Сборы {:,.0f} План {:,.0f} '
          
    elif calculation_type=='ИФЛ':
        title='выполнение  Филиалом плана по ИФЛ {:,.2f}% Сборы {:,.0f} План {:,.0f} '
    elif calculation_type=='Мотивационный план':
        title='выполнение  Филиалом мотивационного плана {:,.2f}% Сборы {:,.0f} План {:,.0f} '
    elif calculation_type=='Железный поток':
        title='выполнение  Филиалом плана по железному потоку {:,.2f}% Сборы {:,.0f} План {:,.0f} '
           
    return {
               'data' : [{'x':df['Отдел'].tolist(),'y':df['ВП'].tolist(), 'type' : 'bar' ,'marker':{'color':'rgba(255, 51, 51,0.5)'}}]
                ,'layout':{'title' : title.format((100*df['Факт'].sum()/df['План'].sum()),df['Факт'].sum(),df['План'].sum())}
                }


'''
@app.callback(
dash.dependencies.Output('download-link','href'),
[dash.dependencies.Input('table','rows')])
def update_download_link(rows):
    df=pd.DataFrame(rows)
    
    csv_string=df.to_csv(index=False,encoding='utf-8')
    csv_string="data:text/csv;charset=utf-8,"+ urllib.parse.quote(csv_string)
    
    
    return csv_string
'''

'''    
@app.server.route('/apps/app6/download')
def download_csv():
    value=flask.request.args.get('value')
    strIO=StringIO.StringIO()
    strIO.write(value)
    strIO.seek(0)
    return send_file(strIO,
    mimetype='text/csv',
    attachment_filename='vp_cbd.csv',
    as_attachment=True)
'''
