import dash
import os
import dash_html_components as html
from flask_caching import Cache


app = dash.Dash(__name__)
server=app.server

CACHE_CONFIG={
    'CACHE_TYPE':'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL','localhost:6379')
}

cache=Cache()
cache.init_app(server,config=CACHE_CONFIG)

app.config.supress_callback_exceptions = True
app.css.config.serve_locally=True
app.scripts.config.serve_locally=True


#server.secret_key=os.environ.get('SECRET_KEY', 'ajiskkjsdkjasfjaffjhsfdkjsfd')

