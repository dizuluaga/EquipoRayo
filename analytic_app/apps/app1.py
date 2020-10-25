from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
from flask import url_for

from app import app

def layout():
    return html.Div([
            html.Div(className='Row',children=[
                html.Div(className='col-lg-12 page-header',children=[
                    html.H3(className='text-center',children='ЗДЕСЬ МОГЛА БЫТЬ АНАЛИТИКА ВАШЕГО ОТДЕЛА!!! ЗВОНИТЕ 061-1113 Пн-Пт с 9 до 18')])
            ]),
            html.Div(className='Row',children=[
                html.Div(className='col-lg-2'),
                html.Div(className='col-lg-8',children=[
                    
                    html.Div(className='col-lg-6',children=[
                        html.Img(className='img-responsive',src='/static/plotly(8).png'),
                        html.Img(className='img-responsive',src='/static/plotly(9).png')
                    ]),
                    html.Div(className='col-lg-6',children=[
                        html.Img(className='img-responsive',src='/static/plotly(10).png'),
                        html.Img(className='img-responsive',src='/static/plotly(12).png')
                    ])
                ]),
                html.Div(className='col-lg-2')
            ])
        ])


