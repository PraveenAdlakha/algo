import logging
import os
from datetime import datetime
import pandas as pd

from dateutil.relativedelta import relativedelta, TH
from kiteconnect import KiteConnect
import time

from src.config import Config

cwd = os.chdir("/Users/padlakha/git/algo")

#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

logging.basicConfig(filename='./logs/vwap_based_straddle_selling.log', filemode='a', format='%(asctime)s - %(message)s',level=logging.DEBUG)


instrumentsList = None

def getCMP(tradingSymbol):
    quote = kite.quote(tradingSymbol)
    if quote:
        return quote[tradingSymbol]['last_price']
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


def getNearestStrikePrice(price, nearestMultiple=50):
    inputPrice = int(price)
    remainder = int(inputPrice % nearestMultiple)
    if remainder < int(nearestMultiple / 2):
        return inputPrice - remainder
    else:
        return inputPrice + (nearestMultiple - remainder)

def getQuote(tradingSymbol):
    quote = kite.quote(tradingSymbol)
    if quote:
        return quote
    else:
        return 0

def sellBankNiftyStraddleAndMonitor( inst_name, qty):
    ATMStrike = getNearestStrikePrice(getCMP('NSE:NIFTY BANK'), 100)
    bankNiftyCE = getQuote("NFO:"+ str(ATMStrike))
    df = pd.read_csv("NFO_Instruments.csv")
    print(df.head())
    next_thursday_expiry = (datetime.today() + relativedelta(weekday=TH(1))).date()
    df1 = df[(df.instrument_type == 'PE' )& (df.name == inst_name) & (df.strike == ATMStrike) & (df.expiry == str(next_thursday_expiry))]
    pe_trading_symbol = ''
    ce_trading_symbol = ''

    for row in df1.itertuples():
        pe_trading_symbol = getattr(row, 'tradingsymbol')

    df1 = df[(df.instrument_type == 'PE') & (df.name == inst_name) & (df.strike == ATMStrike) & (
                df.expiry == str(next_thursday_expiry))]

    for row in df1.itertuples():
        ce_trading_symbol = getattr(row, 'tradingsymbol')

    quote_ce = getQuote("NFO:" + ce_trading_symbol)
    quote_pe = getQuote("NFO:" + pe_trading_symbol)

    avg_quote_ce_price = quote_ce["NFO:"+ ce_trading_symbol]['average_price']
    avg_quote_pe_price = quote_pe["NFO:"+ pe_trading_symbol]['average_price']

    cmp_ce = getCMP("NFO:" + ce_trading_symbol)
    cmp_pe = getCMP("NFO:" + pe_trading_symbol)

    if(cmp_ce+ cmp_pe +10 < avg_quote_pe_price+ avg_quote_ce_price):
        place_order(pe_trading_symbol,0, qty, kite.TRANSACTION_TYPE_SELL, KiteConnect.EXCHANGE_NFO, KiteConnect.PRODUCT_NRML,
                    KiteConnect.ORDER_TYPE_MARKET)
        place_order(ce_trading_symbol,0, qty, kite.TRANSACTION_TYPE_SELL, KiteConnect.EXCHANGE_NFO, KiteConnect.PRODUCT_NRML,
                    KiteConnect.ORDER_TYPE_MARKET)
        while(True):
            time.sleep(2)
            cmp_ce = getCMP("NFO:" + avg_quote_ce_price)
            cmp_pe = getCMP("NFO:" + avg_quote_pe_price)
            quote_ce = getQuote("NFO:" + ce_trading_symbol)
            quote_pe = getQuote("NFO:" + pe_trading_symbol)

            avg_quote_ce_price = quote_ce["NFO:" + ce_trading_symbol]['average_price']
            avg_quote_pe_price = quote_pe["NFO:" + pe_trading_symbol]['average_price']

            if(cmp_ce+ cmp_pe  > avg_quote_pe_price+ avg_quote_ce_price + 5):
                place_order(pe_trading_symbol,0, qty, kite.TRANSACTION_TYPE_BUY, KiteConnect.EXCHANGE_NFO,
                            KiteConnect.PRODUCT_NRML,
                            KiteConnect.ORDER_TYPE_MARKET)
                place_order(ce_trading_symbol,0, qty, kite.TRANSACTION_TYPE_BUY, KiteConnect.EXCHANGE_NFO,
                            KiteConnect.PRODUCT_NRML,
                            KiteConnect.ORDER_TYPE_MARKET)



if __name__ == '__main__':
    # We will sell straddle when its below vwap and do some trailing to bring sl to cost
    # exit when you are in certain profit of 40-50 points it should give better return on wednesday and thursday

    qty = 200
    sellStraddleAndMonitor = sellBankNiftyStraddleAndMonitor('BANKNIFTY', qty)
