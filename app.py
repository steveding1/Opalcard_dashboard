import data
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

app = Dash(__name__)
data.checkmeta()
traindf,stationdf = data.processdata()
maxdate = traindf['MonthYear'].max()
mindate = traindf['MonthYear'].min()

# ------------------------------------------------------------------------------
# App layout
app.layout = html.Div([

    html.H1("Sydey/NSW passenger train stations usage by month", style={'text-align': 'center'}),
    html.H2("From {min} to {max}.".format(min=mindate,max=maxdate), style={'text-align': 'center'}),
    html.A("Data source https://opendata.transport.nsw.gov.au/dataset/train-station-entries-and-exits-data"),

    dcc.Dropdown(id="slct_year",
                 options=[{'label':name, 'value':name} for name in 
                    traindf['MonthYear'].sort_values(ascending=False).unique()],
                 multi=False,
                 value=maxdate,
                 style={'width': "40%"}
                 ),

    html.Div(id='output_container', children=[]),
    
    dcc.Graph(id='my_bee_map', figure={})

])

# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [Output(component_id='output_container', component_property='children'),
     Output(component_id='my_bee_map', component_property='figure')],
    [Input(component_id='slct_year', component_property='value')]
)
def update_graph(option_slctd):

    container = "Current year month is: {}".format(option_slctd)
    MBToken = ''
    px.set_mapbox_access_token(MBToken)

    dff = traindf.copy()
    dff = dff[dff["MonthYear"] == option_slctd].merge(stationdf,on='Station',how='inner')

    print(dff.head(),'\n*******')

    # Plotly Express
    fig = px.scatter_mapbox(
        data_frame=dff,
        lat="LAT", 
        lon="LONG",
        color=(dff['Entry'] - dff['Exit']),
        size=np.sqrt(dff['Entry']),
        text='Station',
        hover_name="Station",
        hover_data={'Entry': True,'Exit': True,"LAT": False,"LONG": False,"Station":False},
        #"size":False,"color":False
        center=dict(lat=-33.88236674,lon=151.2058136),
        height=800,
        zoom=12,
        size_max=45,
        
        color_continuous_scale = px.colors.diverging.Portland
        )

    return container, fig


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)