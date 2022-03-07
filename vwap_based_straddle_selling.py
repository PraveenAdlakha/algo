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

def sellBankNiftyStraddleAndMonitor(ATMStrike):
    bankNiftyCE = getQuote("NFO:"+ str(ATMStrike))
    df = pd.read_csv("NFO_Instruments.csv")
    print(df.head())
    next_thursday_expiry = datetime.today() + relativedelta(weekday=TH(1))




if __name__ == '__main__':
    # We will sell straddle when its below vwap and do some trailing to bring sl to cost
    # exit when you are in certain profit of 40-50 points it should give better return on wednesday and thursday
    BankNiftyATMStrike = getNearestStrikePrice(getCMP('NSE:NIFTY BANK'),100)
    sellStraddleAndMonitor = sellBankNiftyStraddleAndMonitor(BankNiftyATMStrike)
