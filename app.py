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
import copy

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
app.css.append_css({'external_url': 'https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css'})  # noqa: E501

layout = dict(
    autosize=True,
    height=670,
    font=dict(color='#fffcfc'),
    titlefont=dict(color='#fffcfc', size='14'),
    margin=dict(
        l=35,
        r=35,
        b=35,
        t=45
    ),
    hovermode="closest",
    plot_bgcolor="#191A1A",
    paper_bgcolor="#020202",
    legend=dict(font=dict(size=10), orientation='h'),
    title='Hover point in the map to observe street condition',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style="dark",
        center=dict(
            lon=-76.155,
            lat=43.052
        ),
        zoom=11,
    )
)

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
        "layout": layout
    }

# Creating layouts for image and datatable
layout_pic = copy.deepcopy(layout)
layout_pic['height'] = 300
layout_pic['margin-top'] = '10'
layout_pic['max-width'] = 550

layout_right = copy.deepcopy(layout)
layout_right['height'] = 300
layout_right['margin-top'] = '10'


# Layout
app.layout = html.Div([
    # Title - Row
    html.Div(
        [
            html.H1(
                'Street Quality IDentification [SQUID]',
                style={'font-family': 'Helvetica',
                       "margin-top": "25",
                       "margin-bottom": "0"},
                className='eight columns',
            ),
            html.Img(
                src="http://static1.squarespace.com/static/546fb494e4b08c59a7102fbc/t/591e105a6a496334b96b8e47/1497495757314/.png",
                className='two columns',
                style={
                    'height': '9%',
                    'width': '9%',
                    'float': 'right',
                    'position': 'relative',
                    'padding-top': 10,
                    'padding-right': 0
                },
            ),
            html.P(
                'ARGO - Pilot with City of Syracuse - April 2016',
                style={'font-family': 'Helvetica',
                       "font-size": "120%",
                       "width": "80%"},
                className='ten columns',
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
                              style={'margin-top': '10'})
                ], className = "six columns"
            ),
            html.Div(
                [
                    html.Img(id = 'image',
                    style=layout_pic)
                ], className = "six columns"
            ),
            html.Div(
                [
                    dt.DataTable(
                        rows=grouped_tab.to_dict('records'),
                        columns=map_data.ix[:, [0, 3, 7]].columns,
                        row_selectable=True,
                        filterable=False,
                        sortable=True,
                        selected_row_indices=[0, 1, 2],
                        id='datatable'),
                ],
                style=layout_right,
                className="six columns"
            )
        ], className='row'
    )
], className='ten columns offset-by-one')

# Callbacks and functions
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

if __name__ == '__main__':
    app.run_server(debug=True)
