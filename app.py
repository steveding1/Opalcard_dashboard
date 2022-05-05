import imp
from multiprocessing.sharedctypes import Value
from tkinter import Variable
import data
import numpy as np
import plotly.express as px 
import pandas as pd
from dash import Dash, dcc, html, Input, Output

app = Dash(__name__)
data.checkmeta()
traindf,stationdf = data.processdata()
train = pd.read_csv('train.csv')
maxdate = traindf['MonthYear'].max()
mindate = traindf['MonthYear'].min()

# ------------------------------------------------------------------------------
# App layout
app.layout = html.Div([

    html.H1("Sydney/NSW passenger train stations usage by month", style={'text-align': 'center'}),
    html.H2("From {min} to {max}.".format(min=mindate,max=maxdate), style={'text-align': 'center'}),
    html.A('Data source: transport NSW', href="https://opendata.transport.nsw.gov.au/dataset/train-station-entries-and-exits-data"),

    dcc.Dropdown(id="slct_year",
                 options=[{'label':name, 'value':name} for name in 
                    traindf['MonthYear'].sort_values(ascending=False).unique()],
                 multi=False,
                 value=maxdate,
                 style={'width': "30%"}
                 ),

    dcc.Dropdown(id="map_style",
                 options=['open-street-map', 'carto-positron', 'carto-darkmatter', 
                 'stamen-terrain', 'stamen-toner', 'stamen-watercolor',
                 'basic', 'streets', 'outdoors', 'light', 'dark', 'satellite', 'satellite-streets'],
                 multi=False,
                 value='open-street-map',
                 style={'width': "30%"}
                 ),

    html.Div(id='output_container', children=[]),
    
    dcc.Graph(id='bar', figure={}),
    dcc.Graph(id='syd_map', figure={})

])

# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [Output(component_id='output_container', component_property='children'),
     Output(component_id='bar', component_property='figure'),
     Output(component_id='syd_map', component_property='figure')],
    [Input(component_id='slct_year', component_property='value'),
    Input(component_id='map_style', component_property='value')]
)
def update_graph(option_slctd,mapbox_style):

    container = "Current year month is: {}".format(option_slctd)
    MBToken = 'pk. regist and get from plotly.com'
    px.set_mapbox_access_token(MBToken)

    dff = traindf.copy()
    dff = dff.merge(stationdf,on='Station',how='inner')#[dff["MonthYear"] == option_slctd]

#    print(dff.head(),'\n*******')

    # Plotly Express
    fig = px.scatter_mapbox(
        data_frame=dff,
        lat="LAT", 
        lon="LONG",
        color=(dff['Exit'] - dff['Entry']),
        size=np.sqrt(dff['Entry']),
        labels=dict(color="Exit minus Entry"),
        text='Station',
        hover_name="Station",
        hover_data={'Entry': True,'Exit': True,"LAT": False,"LONG": False,"Station":False,"MonthYear":False},
        center=dict(lat=-33.88236674,lon=151.2058136),
        height=1000,
        zoom=12,
        size_max=40,
        mapbox_style=mapbox_style,
        color_continuous_scale = px.colors.diverging.Portland,
        animation_frame="MonthYear",
        animation_group="Station"
        )
    
    dff2 = traindf[traindf['MonthYear']==option_slctd].sort_values('Entry',ascending=False).head(15)
    bar = px.bar(dff2, x="Station", y=["Entry","Exit"], barmode="group",
    labels=dict(Station="Train station", value="Monthly Taps", variable="Directions"))
    bar.update_traces(hovertemplate="<br>".join(["Station: %{x}","Taps: %{y}"]))

    return container, bar, fig

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
