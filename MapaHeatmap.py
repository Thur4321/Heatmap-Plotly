import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
from collections import OrderedDict
from metpy.interpolate import interpolate_to_grid, remove_repeat_coordinates
import json
import urllib
with urllib.request.urlopen('https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-35-mun.json') as response:
    geo = json.load(response)
from itertools import chain
    
app = dash.Dash(__name__)

a = []
for i in range(0, len(geo['features'])):
    a.append(geo['features'][i]['geometry']['coordinates'])
lista = list(chain(*a))
lista1 = list(chain(*lista))
lista2 = []
for i in range(0, len(lista1)):
    for j in lista1[i]:
        lista2.append(j)
latitudes = []
longitudes = []

for i in range(0, len(lista2)):
    if i%2 == 0:
        longitudes.append(lista2[i])
    else:
        latitudes.append(lista2[i])

d = {'lat':[-53.56715035800035,-43.50425639281976], 'lon':[-19.55515153508422,-25.594132282758494], 'preci': [0, 0]} 
dfcoord = pd.DataFrame(d)

colnames = ['Munic','code','uf','nome_est','lat','lon','data','preci','nan']
df=pd.read_csv("data.csv", sep=';', names=colnames) 
df = df.iloc[1: , :].reset_index(drop=True)
df = df.replace({',':'.'}, regex = True)
del df['nan']
df['data'], df['hora'] = df['data'].str.split(' ', 1).str
df['data'] = df['data'].astype(str, errors = 'raise')
df['preci'] = df['preci'].astype(float, errors = 'raise')
df['lat'] = df['lat'].astype(float, errors = 'raise')
df['lon'] = df['lon'].astype(float, errors = 'raise')
df['Munic'] = df['Munic'].str.capitalize()
df = df.groupby(['Munic', 'code', 'uf', 'nome_est', 'lat', 'lon', 'data']).agg({'preci':'sum'}).reset_index()
datalist = list(OrderedDict.fromkeys(df['data'].tolist()))

app.layout = html.Div([
    html.H1('Web Application Dashboards with Dash', style = {'text-align':'center'}),
    dcc.Dropdown(id = 'slct_day',
                options = datalist,
                multi = False,
                value = '2022-02-01',
                style = {'width':'40%'}
                ),
    html.Div(id = 'output_container', children = []),
    html.Br(),
    dcc.Graph(id = 'Rain_Map', figure = {})
    
])

@app.callback(
    [Output(component_id = 'output_container', component_property = 'children'),
     Output(component_id = 'Rain_Map', component_property = 'figure')],
    [Input(component_id = 'slct_day', component_property = 'value')]
)
def update_graph(option_slctd):
    print(option_slctd)
    print(type(option_slctd))
     
    container = 'O dia escolhido pelo usuário é: {}'.format(option_slctd)
     
    dff = df.copy()
    dff = dff[dff['data'] == option_slctd]
    dff = pd.concat([dfcoord, dff]).reset_index(drop = True)
    
    lat=dff.lat.tolist()
    lon=dff.lon.tolist()
    pre=dff.preci.tolist()
    la=[]
    lo=[]
    pr =[]
    for i in range(0,len(dff)):
        la.append(lat[i])
        lo.append(lon[i])
        pr.append(pre[i])
        
    x, y, z = remove_repeat_coordinates(la, lo, pr)
        
    gx, gy, img = interpolate_to_grid(x, y, z, interp_type= 'rbf', 
                                              rbf_smooth = 10,
                                              hres=0.01)
    
    for i in range(0, len(img)):
        for j in range(0, len(img[0])):
            if img[i, j] < 0:
                img[i, j] = 0
     
    gx1 = gx.ravel().tolist()
    gy1 = gy.ravel().tolist()
    img1 = img.ravel().tolist()
    
    fig = go.Figure(data = go.Heatmap(x = gx1, y = gy1, z = img1, colorscale = 'Blues')) 
    
    fig.update_xaxes(
        tickangle = 90,
        title_text = "Longitude",
        title_font = {"size": 20},
        title_standoff = 25)

    fig.update_yaxes(
        title_text = "Longitude",
        title_standoff = 25)
    
    fig.add_scatter(x = longitudes, y = latitudes, mode="markers",
                marker=dict(size=1, color="Black"), hoverinfo='none') 
    
    fig.update_layout(autosize = False, width = 720, height = 480)
    
    return container, fig

if __name__ == '__main__':
    app.run_server(port = 8000, debug=True, use_reloader=True)



