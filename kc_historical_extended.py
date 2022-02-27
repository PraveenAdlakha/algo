# -*- coding: utf-8 -*-
"""
Zerodha Kite Connect - Fetching Historical Data over extended duration

@author: Mayank Rasu (http://rasuquant.com/wp/)

To run this need to subscribe to the historical api
"""
from kiteconnect import KiteConnect
import os
import datetime as dt
import pandas as pd

cwd = os.chdir("/Users/padlakha/git/algo")

#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)


#get dump of all NSE instruments
instrument_dump = kite.instruments("NSE")
instrument_df = pd.DataFrame(instrument_dump)
#instrument_df.to_csv("NSE_Instruments_31122019.csv",index=False)


def instrumentLookup(instrument_df,symbol):
    """Looks up instrument token for a given script from instrument dump"""
    try:
        return instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]
    except:
        return -1


def fetchOHLCExtended(ticker,inception_date, interval):
    """extracts historical data and outputs in the form of dataframe
       inception date string format - dd-mm-yyyy"""
    instrument = instrumentLookup(instrument_df,ticker)
    from_date = dt.datetime.strptime(inception_date, '%d-%m-%Y')
    to_date = dt.date.today()
    data = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    while True:
        if from_date.date() >= (dt.date.today() - dt.timedelta(100)):
            data = data.append(pd.DataFrame(kite.historical_data(instrument,from_date,dt.date.today(),interval)),ignore_index=True)
            break
        else:
            to_date = from_date + dt.timedelta(100)
            data = data.append(pd.DataFrame(kite.historical_data(instrument,from_date,to_date,interval)),ignore_index=True)
            from_date = to_date
    data.set_index("date",inplace=True)
    return data


ohlc = fetchOHLCExtended("INFY","20-08-2019","5minute")