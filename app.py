#######################################################
# Main APP definition.
#
# Dash Bootstrap Components used for main theme and better
# organization.
#######################################################

import dash
import dash_bootstrap_components as dbc

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,FONT_AWESOME], title='Equipo Rayo', update_title=None)
server = app.server

# We need this for function callbacks not present in the app.layout
app.config.suppress_callback_exceptions = True
