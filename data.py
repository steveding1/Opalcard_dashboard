import pandas as pd
import requests
import numpy as np

TRAIN_URL = 'https://opendata.transport.nsw.gov.au/api/download/2df8f461-67d3-45f7-8837-16fa71c8143f'
SATATION_URL = 'https://opendata.transport.nsw.gov.au/api/download/ed849af1-59a6-42e7-826b-76713315a9fe'
META_URL = 'https://opendata.transport.nsw.gov.au/dataset/train-station-entries-and-exits-data'
META_LOG = "modified.log"
LOGIN_URL = 'https://opendata.transport.nsw.gov.au/user/login'
LOGIN_USER = 'sweetstar'
LOGIN_PWD = '****' #regist a free account from https://opendata.transport.nsw.gov.au/

def down_csv(login_url,user,pwd):
        """check metadata, login website and download the csv.
        
        Args:
                login_url: a string start with https://
                user: website's login 
                pwd: login's password

        Returns:
                2 dataframes: train-opal and stations' long/lat
        """
        print('download start...')
        data = {'name': user,
                'pass': pwd,
                'form_build_id': 'form-9ylwT__-7dtpac3MwQL_T0RSAIJmkAgVZ6sBH5Hy6yw',
                'form_id': 'user_login',
                'op': 'Log in'}
        headers = {'User-agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'}
        session = requests.Session()
        resp = session.post(login_url, data=data, headers=headers)
        if resp.status_code!=200:
          print('login failed')
          return -1
        print('login ok')
        print('dowloading train.csv')
        content = session.get(TRAIN_URL, headers=headers)
        with open("train.csv","w",newline='\n') as f:
                f.write(content.text)
        print('dowloading station.csv')
        content = session.get(SATATION_URL, headers=headers)
        with open("station.csv","w",newline='\n') as f:
                f.write(content.text)

#compare the metadata with .log, if changed download the new csv.
def checkmeta():
        data =pd.read_html(META_URL)
        modified = data[0].iloc[0,1]+','+data[0].iloc[3,1]
        with open(META_LOG,"r+") as f:
                last = f.readlines()[-1]
        if modified == last:
                print('No new data')
        else:
                print('Updates the data files')
                f.write('\n'+modified)
                down_csv(LOGIN_URL, LOGIN_USER, LOGIN_PWD)

def processdata():
        """
        ReadCSV and process the dataframes.

        Returns:
                2 dataframes: train-opal and stations' long/lat
        """
        #data transfering begins
        traindf = pd.read_csv('train.csv')
        stationdf = pd.read_csv('station.csv')
        stationdf.rename(columns={"Train_Station":"Station"}, inplace=True)
        print('The newest month is',traindf['MonthYear'].max())

        #simplify stationdf by averaging LAT and LONG of mutiple entrances of each stations
        stationdf.drop(columns=['Street_Name','Street_Type','Entrance_Type','Exit_Number'],inplace=True)
        stationdf = stationdf.groupby('Station').mean(['LAT','LONG'])
        stationdf = stationdf.reset_index()

        #Set 'Less than 50' to 0
        traindf['Trip'].mask(traindf['Trip'] == 'Less than 50',other=0,inplace=True)
        traindf['Trip'] = traindf['Trip'].astype('int')
        traindf.Station = traindf.Station.str.replace(' Station', '')

        #Fixing missing stations
        to_replace = ['Chester Hil','Wolli','Mount Kurring-gai','Leppingon',
        'Shellharbour','Ersineville','Wirragula']
        value = ['Chester Hill','Wolli Creek', 'Mount Kuring-gai', 'Leppington',
        'Shellharbour Junction', 'Erskineville','Wirragulla']
        stationdf = stationdf.replace(to_replace=to_replace, value=value)
        bathurst = pd.DataFrame([['Bathurst',-33.425556,149.583333]],columns=['Station','LAT','LONG'])
        zigzag = pd.DataFrame([['Zig Zag',-33.470556,150.200556]],columns=['Station','LAT','LONG'])
        stationdf = pd.concat([stationdf,bathurst,zigzag]).sort_values('Station')

        stations = set(stationdf.Station.unique())
        stations1 = set(traindf.Station.unique())
#        stations1 = set([station.replace(' Station','') for station in stations1])
        print('There are {} stations in the traffic data'.format(len(stations1)))
        print('There are {} stations in the station list'.format(len(stations)))
        print('The station not in station list are', stations1-stations)
        
        #MonthYear to_date?
        traindf = traindf.pivot(index=['MonthYear','Station'],columns='Entry_Exit',values='Trip').reset_index()
#        traindf["Date"] = pd.to_datetime(traindf["MonthYear"] ,format="%Y-%m")
#        traindf["Date"] = traindf["Date"].apply(lambda x: x.strftime("%b-%Y"))

        #print(final.head())
        return traindf,stationdf
