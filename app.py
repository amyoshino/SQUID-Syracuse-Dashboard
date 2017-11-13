# -*- coding: utf-8 -*-
import dash
from dash.dependencies import Input, Output, State, Event
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import plotly
from plotly import graph_objs as go
from plotly.graph_objs import *
import flask
import pandas as pd
import numpy as np
import os
import datetime

app = dash.Dash(__name__)
server = app.server

# API keys and datasets
mapbox_access_token = 'pk.eyJ1IjoiYW15b3NoaW5vIiwiYSI6ImNqOXA3dGF2bDJhMjMyd2xnNTJqdXFxc2sifQ.9SoIXAYOZ8qfTiHaw6rWmg'
map_data = pd.read_csv('SQUID-SYRACUSE-MASTER - FINAL-APR29-SPEEDgt5.csv - SQUID-SYRACUSE-MASTER - FINAL-APR29-SPEEDgt5.csv')
map_data['Timestamp'] = map_data['Timestamp'].apply(lambda x : datetime.datetime.fromtimestamp(int(x)).strftime('%Y-%m-%d'))
map_data.columns = ['Date', 'Latitude', 'Longitude', 'Speed', 'X', 'Y', 'Z', 'Ride_Quality', 'Image_Name',
       'Image', 'Street_Name']
grouped_tab = map_data.ix[:, [0, 3, 7]].groupby('Date', as_index = False).mean()

#map_data.drop("Unnamed: 0", 1, inplace=True)

# Boostrap CSS.
app.css.append_css({"external_url": "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css"})
# Extra Dash styling.
app.css.append_css({"external_url": 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
# JQuery is required for Bootstrap.
app.scripts.append_script({"external_url": "https://code.jquery.com/jquery-3.2.1.min.js"})
# Bootstrap Javascript.
app.scripts.append_script({"external_url": "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"})

# Components style
def color_scale(map_data):
    color = []
    max_score = map_data['Ride_Quality'].max()
    min_score = map_data['Ride_Quality'].min()
    for row in map_data['Ride_Quality']:
        color.append((row - min_score)/(max_score - min_score))
    return color

def gen_map(map_data):
    # groupby returns a dictionary mapping the values of the first field
    # 'classification' onto a list of record dictionaries with that
    # classification value.
    return {
        "data": [
                {
                    "type": "scattermapbox",
                    "lat": list(map_data['Latitude']),
                    "lon": list(map_data['Longitude']),
                    "text": list(map_data['Date']),
                    "mode": "markers",
                    "name": list(map_data['Ride_Quality']),
                    "marker": {
                        "size": 3,
                        "opacity": 0.8,
                        "color": color_scale(map_data),
                        "colorscale": 'GnYlRd'
                    }
                }
            ],
        "layout": {
            "height": 850,
            "width": 750,
            "hovermode": "closest",
            "mapbox": {
                "accesstoken": mapbox_access_token,
                "bearing": 0,
                "center": {
                    "lat": 43.052,
                    "lon": -76.155
                },
                "pitch": 0,
                "zoom": 11,
                "style": "dark"
            }
        }
    }


# Layout
app.layout = html.Div([
    # Title - Row
    html.Div(
        [
            html.H1(
                'Street Quality IDentification [SQUID]',
                style={'font-family': 'Helvetica',
                       "text-align": "right",
                       "width": "1050",
                       "margin-top": "25",
                       "margin-bottom": "0",
                       "font-size": "280%"},
                className='col-md-10',
            ),
            html.Img(
                src="http://static1.squarespace.com/static/546fb494e4b08c59a7102fbc/t/591e105a6a496334b96b8e47/1497495757314/.png",
                className='col-md-2',
                style={
                    'height': '100',
                    'width': '135',
                    'float': 'right',
                    'position': 'float',
                    "margin-right": "20"
                },
            ),
            html.P(
                'ARGO',
                style={'font-family': 'Helvetica',
                       "text-align": "center",
                       "font-size": "120%"},
                className='col-md-12',
            ),
            html.P(
                'Pilot with City of Syracuse - April 2016',
                style={'font-family': 'Helvetica',
                       "text-align": "center",
                       "font-size": "120%"},
                className='col-md-12',
            ),
        ],
        className='row'
    ),

    # Map + image + table
    html.Div(
        [
            html.Div(
                [
                    dcc.Graph(id='map-graph',
                              figure = gen_map(map_data),
                              style={'font-family': 'Helvetica',
                                    "text-align": "center",
                                    "font-size": "30%"})
                ], className = "col-md-5"
            ),
            html.Div(
                [
                    html.Img(id = 'image',
                    style={'max-width': '90%', 'max-height': '90%', 'height': 400,
                            'padding-top': '100', 'padding-left': '100',
                            'margin-left': 'auto', 'margin-right': 'auto'})
                ], className = "col-md-7"
            ),
            html.Div(
                [
                    dt.DataTable(
                        rows=grouped_tab.to_dict('records'),
                        columns=map_data.ix[:, [0, 3, 7]].columns,
                        row_selectable=True,
                        filterable=False,
                        sortable=True,
                        selected_row_indices=[],
                        id='datatable'),
                ],
                style={'width': '44%', "font-size": 11, "height": 100,
                    "margin-top": 0, "padding-top": 10, "padding-left": 115},
                className="col-md-7"
            )
        ], className="col-md-12"
    )
])

def dfRowFromHover( hoverData ):
    ''' Returns row for hover point as a Pandas Series '''
    if hoverData is not None:
        if 'points' in hoverData:
            firstPoint = hoverData['points'][0]
            if 'pointNumber' in firstPoint:
                point_number = firstPoint['pointNumber']
                row = map_data.iloc[point_number]
                return row
    return pd.Series()

@app.callback(
    dash.dependencies.Output('image', 'src'),
    [dash.dependencies.Input('map-graph', 'hoverData')])
def update_image_src(map_hover):
    row = dfRowFromHover(map_hover)
    if row.empty:
        img_src = "https://s3-us-west-2.amazonaws.com/argosquid/SYRACUSE/images/1460742669.0.jpg"
        return img_src
    img_src = row['Image']
    return img_src

@app.callback(
    Output('map-graph', 'figure'),
    [Input('datatable', 'rows'),
     Input('datatable', 'selected_row_indices')])
def map_selection(rows, selected_row_indices):
    if len(selected_row_indices) == 0:
        return gen_map(map_data)
    else:
        print (selected_row_indices)
        date = list(grouped_tab.ix[selected_row_indices,:]['Date'])
        temp_df = map_data[map_data['Date'].isin(date)]
        return gen_map(temp_df)

@app.callback(
    Output('datatable', 'selected_row_indices'),
    [Input('map-graph', 'clickData')],
    [State('datatable', 'selected_row_indices')])
def update_selected_row_indices(clickData, selected_row_indices):
    if clickData:
        for point in clickData['points']:
            if point['pointNumber'] in selected_row_indices:
                selected_row_indices.remove(point['pointNumber'])
            else:
                selected_row_indices.append(point['pointNumber'])
    return selected_row_indices

#def serve_image(image_path):
#    image_name = '{}.png'.format(image_path)
#    if image_name not in list_of_images:
#        raise Exception('"{}" is excluded from the allowed static files'.format(image_path))
#    return flask.send_from_directory(image_directory, image_name)

if __name__ == '__main__':
    app.run_server(debug=True)
