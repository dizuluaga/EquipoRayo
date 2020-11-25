import dash_bootstrap_components as dbc
import dash_html_components as html

# Recall app
import app

card_camilo = dbc.Card(
    [
        dbc.CardImg(src="/assets/camilo.jpg", top=True),
        dbc.CardBody(
            [
                html.H5("Camilo Gutiérrez Ramírez", className="card-title"),
                html.P(
                    "Front End Developer",
                    className="card-text",
                ),
                dbc.Button(
                    "Contact me",
                    className="mr-1",
                    href="https://www.linkedin.com/in/cagutierrezra/",
                    target="_blank",
                ),
            ]
        ),
    ],
    style={"width": "18rem", "textAlign": "center"},
)

card_diana = dbc.Card(
    [
        dbc.CardImg(src="/assets/diana.jpg", top=True),
        dbc.CardBody(
            [
                html.H5("Diana Zuluaga Pulgarín", className="card-title"),
                html.P(
                    "Front End Developer",
                    className="card-text",
                ),
                dbc.Button(
                    "Contact me",
                    className="mr-1",
                    href="https://www.linkedin.com/in/diana-zuluaga-pulgarin/",
                    target="_blank",
                ),
            ]
        ),
    ],
    style={"width": "18rem", "textAlign": "center"},
)

card_julian = dbc.Card(
    [
        dbc.CardImg(src="/assets/julian.jpeg", top=True),
        dbc.CardBody(
            [
                html.H5("Julián Arango Ochoa", className="card-title"),
                html.P(
                    "Front End Developer",
                    className="card-text",
                ),
                dbc.Button(
                    "Contact me",
                    className="mr-1",
                    href="https://www.linkedin.com/in/jarangoo/",
                    target="_blank",
                ),
            ]
        ),
    ],
    style={"width": "18rem", "textAlign": "center"},
)

card_wbeimar = dbc.Card(
    [
        dbc.CardImg(src="/assets/wbeimar.jpeg", top=True),
        dbc.CardBody(
            [
                html.H5("Wbeimar Ossa Giraldo", className="card-title"),
                html.P(
                    "Back End Developer",
                    className="card-text",
                ),
                dbc.Button(
                    "Contact me",
                    className="mr-1",
                    href="https://www.linkedin.com/in/wbeimarossa",
                    target="_blank",
                ),
            ]
        ),
    ],
    style={"width": "18rem", "textAlign": "center"},
)

card_edison = dbc.Card(
    [
        dbc.CardImg(src="/assets/edison.jpeg", top=True),
        dbc.CardBody(
            [
                html.H5("Edison Yepes Sánchez", className="card-title"),
                html.P(
                    "Back End Developer",
                    className="card-text",
                ),
                dbc.Button(
                    "Contact me",
                    className="mr-1",
                    href="https://www.linkedin.com/in/edison-yepes/",
                    target="_blank",
                ),
            ]
        ),
    ],
    style={"width": "18rem", "textAlign": "center"},
)

layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(card_camilo, xl=3, width = 9, align='start'),
                dbc.Col(card_diana, xl=3, width = 9,align='start'),
                dbc.Col(card_wbeimar, xl=3, width = 9,align='start'),
            ],
            justify="center",
        ),
        dbc.Row(
            [
                dbc.Col(card_julian, xl=3, width = 9,align='center'),
                dbc.Col(card_edison, xl=3, width = 9,align='center'),
            ],
            justify="center",style={'margin-top':'30px'}
        )
    ],className="ds4a-body",
)  # justify="start", "center", "end", "between", "around"
