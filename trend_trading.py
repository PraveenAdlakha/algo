# -*- coding: utf-8 -*-
"""
Zerodha Kite Connect - RSI implementation

@author: Mayank Rasu (http://rasuquant.com/wp/)
"""
from kiteconnect import KiteConnect
import pandas as pd
import datetime as dt
import os
import numpy as np
import logging
import time
from datetime import datetime
import requests

cwd = os.chdir("/Users/padlakha/git/algo")

#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

#get dump of all NSE instruments
#instrument_dump = kite.instruments("NSE")
instrument_df = pd.read_csv("NFO_Instruments.csv")

logging.basicConfig(filename='./logs/DJ_Bhai_ka_algo.log', filemode='a', format='%(asctime)s - %(message)s',level=logging.DEBUG)

telegram_path = "telegram.config"
telegram_settings = open(telegram_path, 'r').read().split()

def instrumentLookup(instrument_df,symbol):
    """Looks up instrument token for a given script from instrument dump"""
    try:
        return instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]
    except:
        return -1


def fetchOHLC(ticker,interval,duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    data = pd.DataFrame(kite.historical_data(instrument,dt.date.today()-dt.timedelta(duration), dt.date.today(),interval))
    data.set_index("date",inplace=True)
    return data


def rsi(df, n):
    "function to calculate RSI"
    delta = df["close"].diff().dropna()
    u = delta * 0
    d = u.copy()
    u[delta > 0] = delta[delta > 0]
    d[delta < 0] = -delta[delta < 0]
    u[u.index[n-1]] = np.mean( u[:n]) # first value is average of gains
    u = u.drop(u.index[:(n-1)])
    d[d.index[n-1]] = np.mean( d[:n]) # first value is average of losses
    d = d.drop(d.index[:(n-1)])
    rs = u.ewm(com=n,min_periods=n).mean()/d.ewm(com=n,min_periods=n).mean()
    return 100 - 100 / (1+rs)

def MACD(DF,a,b,c):
    """function to calculate MACD
       typical values a(fast moving average) = 12;
                      b(slow moving average) =26;
                      c(signal line ma window) =9"""
    df = DF.copy()
    df["MA_Fast"]=df["close"].ewm(span=a,min_periods=a).mean()
    df["MA_Slow"]=df["close"].ewm(span=b,min_periods=b).mean()
    df["MACD"]=df["MA_Fast"]-df["MA_Slow"]
    df["Signal"]=df["MACD"].ewm(span=c,min_periods=c).mean()
    df.dropna(inplace=True)
    return df

def EMAVol(DF,moving_avg):
    df = DF.copy()
    return df

def getMovingAvgValue(DF, moving_avg):
    df = DF.copy()
    moving_avg_value = df["close"].ewm(span=moving_avg,min_periods=moving_avg).mean()
    return moving_avg_value


def getVolumeMovingAvgValue(DF, moving_avg):
    df = DF.copy()
    moving_avg_value = df["volume"].ewm(span=moving_avg,min_periods=moving_avg).mean()
    return moving_avg_value

def getCMP(tradingSymbol):
    quote = kite.quote(tradingSymbol)
    if quote:
        return quote[tradingSymbol]['last_price']
    else:
        return 0

def getQuote(tradingSymbol):
    quote = kite.quote(tradingSymbol)
    if quote:
        return quote
    else:
        return 0

def place_order(tradingSymbol, price, qty, transaction_type, exchangeType, product, orderType):
    try:
        orderId = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=exchangeType,
            tradingsymbol=tradingSymbol,
            transaction_type=transaction_type,
            quantity=qty,
            price=price,
            product=product,
            order_type=orderType)

        logging.debug('Order placed successfully, orderId = %s', orderId)
        return orderId
    except Exception as e:
        logging.debug('Order placement failed: %s', e.message)


def findTrade(trading_symbol, qty):
    ohlc = fetchOHLC(trading_symbol, "5minute", 2)
    macd = MACD(ohlc, 12, 26, 9)
    bought = 0
    now = datetime.now()
    start_time = now.replace(hour=9, minute=21, second=0, microsecond=0)
    end_time = now.replace(hour=11, minute=25, second=0, microsecond=0)

    while (datetime.now() < start_time) :
        time.sleep(10)
        logging.debug("Wating for starttime:" + start_time.strftime("%m/%d/%Y, %H:%M:%S") + " right now its :  " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    while(True):
        ohlc = fetchOHLC(trading_symbol, "5minute", 5)
        rsi_v = rsi(ohlc, 14)
        rsi_value = rsi_v.iat[-1]
        print("rsi:" + str(rsi_value))
        ten_moving_avg = getMovingAvgValue(ohlc, 10).iat[-1]
        print("10 moving avg:" + str(ten_moving_avg))
        twenty_moving_avg = getMovingAvgValue(ohlc, 20).iat[-1]
        print("20 moving avg:" + str(twenty_moving_avg))

        quote = getQuote("NFO:" + trading_symbol)
        avg_quote_ce_price = quote["NFO:" + trading_symbol]['average_price']
        print("vwap:" + str(avg_quote_ce_price))

        volume_moving_avg = getVolumeMovingAvgValue(ohlc, 20)
        volume_moving_avg_value = volume_moving_avg.iat[-1]
        print("volume_moving_avg:" + str(volume_moving_avg.iat[-1]))
        current_volume = ohlc.tail(1)["volume"]
        logging("RSI:" + str(rsi_value) + " current_volume:" + str(
            current_volume) + " volume_avg_value" + str(volume_moving_avg_value)
                + "10  moving avg:" + str(ten_moving_avg) + " 20 moving_avg:" + str(
            twenty_moving_avg) + " time:" + datetime.now())
        if (rsi_value > 60 and current_volume > volume_moving_avg_value and ten_moving_avg > twenty_moving_avg):
            logging("Got buy signal.. RSI:" + str(rsi_value) + " current_volume:" + str(current_volume) + " volume_avg_value" + str(volume_moving_avg_value)
                    + "10  moving avg:" + str(ten_moving_avg) + " 20 moving_avg:" + str(twenty_moving_avg) + " time:"+ datetime.now())
            telegram_url = telegram_settings[0].format("Got buy signal.. RSI:" + str(rsi_value) + " current_volume:" + str(current_volume) + " volume_avg_value" + str(volume_moving_avg_value)
                    + "10  moving avg:" + str(ten_moving_avg) + " 20 moving_avg:" + str(twenty_moving_avg) + " time:"+ datetime.now())
            requests.get(telegram_url)
            # place_order(trading_symbol, 0, qty, kite.TRANSACTION_TYPE_BUY, KiteConnect.EXCHANGE_NFO,
            #                KiteConnect.PRODUCT_NRML,KiteConnect.ORDER_TYPE_MARKET)
            bought = 1
            monitor(trading_symbol, qty, bought)
        if (rsi_value < 40 and current_volume > volume_moving_avg_value and ten_moving_avg < twenty_moving_avg):
            logging("Got sell signal.. RSI:" + str(rsi_value) + " current_volume:" + str(
                current_volume) + " volume_avg_value" + str(volume_moving_avg_value)
                    + "10  moving avg:" + str(ten_moving_avg) + " 20 moving_avg:" + str(
                twenty_moving_avg) + " time:" + datetime.now())
            telegram_url = telegram_settings[0].format("Got sell signal.. RSI:" + str(rsi_value) + " current_volume:" + str(
                current_volume) + " volume_avg_value" + str(volume_moving_avg_value)
                    + "10  moving avg:" + str(ten_moving_avg) + " 20 moving_avg:" + str(
                twenty_moving_avg) + " time:" + datetime.now())
            requests.get(telegram_url)
            # place_order(trading_symbol, 0, qty, kite.TRANSACTION_TYPE_SELL, KiteConnect.EXCHANGE_NFO,
            #                KiteConnect.PRODUCT_NRML,KiteConnect.ORDER_TYPE_MARKET)
            bought = 1
            monitor(trading_symbol, qty, bought)

def monitor(trading_symbol, qty, bought):
    if(bought):
        while(True):
            ohlc = fetchOHLC(trading_symbol, "5minute", 2)
            ten_moving_avg = getMovingAvgValue(ohlc, 10).iat[-1]
            twenty_moving_avg = getMovingAvgValue(ohlc, 20).iat[-1]
            if(ten_moving_avg < twenty_moving_avg):
                telegram_url = telegram_settings[0].format("got exit Signal ten moving avg < twenty"+ str(getCMP(trading_symbol)))
                requests.get(telegram_url)
                # place_order(trading_symbol, 0, qty, kite.TRANSACTION_TYPE_SELL, KiteConnect.EXCHANGE_NFO,
                #             KiteConnect.PRODUCT_NRML, KiteConnect.ORDER_TYPE_MARKET)
                break
            logging.debug("We are in buy 10 moving :" + str(ten_moving_avg) + " 20 moving avg:" + twenty_moving_avg + " time:"+ datetime.now())
            time.sleep(300)
    else:
        while(True):
            ohlc = fetchOHLC(trading_symbol, "5minute", 2)
            ten_moving_avg = getMovingAvgValue(ohlc, 10).iat[-1]
            twenty_moving_avg = getMovingAvgValue(ohlc, 20).iat[-1]
            if (ten_moving_avg > twenty_moving_avg):
                telegram_url = telegram_settings[0].format("got exit Signal ten moving avg > twenty" + str(getCMP(trading_symbol)))
                requests.get(telegram_url)
                # place_order(trading_symbol, 0, qty, kite.TRANSACTION_TYPE_BUY, KiteConnect.EXCHANGE_NFO,
                #             KiteConnect.PRODUCT_NRML, KiteConnect.ORDER_TYPE_MARKET)
                break
            logging.debug("We are in sell 10 moving avg :" + str(ten_moving_avg) + " 20 moving avg:" + twenty_moving_avg+ " time:"+ datetime.now())
            time.sleep(300)

if __name__ == '__main__':
    trading_symbol = "BANKNIFTY22MARFUT"
    qty = 25
    # rsi> 60 vol> 20EMA and 10 EMA > 20 EMA buy and reverse for sell exit when crossover happens for 10 and 20
    findTrade(trading_symbol, qty)


