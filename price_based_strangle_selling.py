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

logging.basicConfig(filename='./logs/price_based_strangle_selling.log', filemode='a', format='%(asctime)s - %(message)s',level=logging.DEBUG)


instrumentsList = None

def getCMP(tradingSymbol):
    quote = kite.quote(tradingSymbol)
    if quote:
        return quote[tradingSymbol]['last_price']
    else:
        return 0


def get_symbols(expiry, name, strike, ins_type):
    global instrumentsList

    if instrumentsList is None:
        instrumentsList = kite.instruments('NFO')

    instrument_df = pd.DataFrame(instrumentsList)
    instrument_df.to_csv("NFO_Instruments.csv", index=False)

    lst_b = [num for num in instrumentsList if num['expiry'] == expiry and num['strike'] == strike
             and num['instrument_type'] == ins_type and num['name'] == name]
    return lst_b[0]['tradingsymbol']


def getNearestCEStrikeByPrice(expiry, name, strike,ins_type , price):
    global instrumentsList
    atmStrike = strike
    current_strike = int(strike) + 100

    if instrumentsList is None:
        instrumentsList = kite.instruments('NFO')

    for num in instrumentsList:
        if num['expiry'] == expiry and num['strike'] == current_strike and num['instrument_type'] == ins_type and num['name'] == name:
            current_strike = current_strike + 100
            if num['last_price'] <= price:
                return num['tradingsymbol']


def getNearestPEStrikeByPrice(expiry, name, strike,ins_type , price):
    global instrumentsList
    atmStrike = strike
    current_strike = int(strike) - 100

    if instrumentsList is None:
        instrumentsList = kite.instruments('NFO')

    for num in instrumentsList:
        if num['expiry'] == expiry and num['strike'] == current_strike and num['instrument_type'] == ins_type and num['name'] == name:
            current_strike = current_strike - 100
            if num['last_price'] <= price:
                return num['tradingsymbol']


def getNearestStrikePrice(price, nearestMultiple=50):
       inputPrice = int(price)
       remainder = int(inputPrice % nearestMultiple)
       if remainder < int(nearestMultiple / 2):
           return inputPrice - remainder
       else:
           return inputPrice + (nearestMultiple - remainder)


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

        logging.INFO('Order placed successfully, orderId = %s', orderId)
        return orderId
    except Exception as e:
        logging.INFO('Order placement failed: %s', e.message)


def timeBasedStraddleSelling(start_time, end_time, price, stop_loss, lots):


    if(now > start_time):
        BankNiftyATMStrike = getNearestStrikePrice(getCMP('NSE:NIFTY BANK'), 100)
        bank_nifty_symbol_ce = getNearestCEStrikeByPrice(next_thursday_expiry.date(), 'BANKNIFTY', BankNiftyATMStrike,
                                                         'CE',
                                                         price)
        bank_nifty_symbol_pe = getNearestPEStrikeByPrice(next_thursday_expiry.date(), 'BANKNIFTY', BankNiftyATMStrike,
                                                         'PE',price)
        logging.debug("Placing order for:" + bank_nifty_symbol_ce)
        logging.debug("Placing order for:"+ bank_nifty_symbol_pe)
        #time.sleep(5)

        # place_order(bank_nifty_symbol_ce, 0, lots, kite.TRANSACTION_TYPE_SELL, KiteConnect.EXCHANGE_NFO, KiteConnect.PRODUCT_MIS,
        #             KiteConnect.ORDER_TYPE_MARKET)
        #
        # place_order(bank_nifty_symbol_pe, 0, lots, kite.TRANSACTION_TYPE_SELL, KiteConnect.EXCHANGE_NFO, KiteConnect.PRODUCT_MIS,
        #             KiteConnect.ORDER_TYPE_MARKET)

        monitorStrangleSold(end_time, bank_nifty_symbol_pe, bank_nifty_symbol_ce, stop_loss, lots)


def monitorStrangleSold(end_time, bank_nifty_symbol_pe, bank_nifty_symbol_ce, stop_loss, lots):

    pos_df = pd.DataFrame(kite.positions()["net"])
    #TODO change it to day net is for older position
    #pos_df = pd.DataFrame(kite.positions()["day"])

    bank_nifty_symbol_pe = "NIFTY22MAR17800CE"
    bank_nifty_symbol_ce = "NIFTY22MAR17800CE"

    filter_pe = pos_df[pos_df["tradingsymbol"]== bank_nifty_symbol_pe]
    filter_ce = pos_df[pos_df["tradingsymbol"]== bank_nifty_symbol_ce]

    sold_ce_price = filter_pe["average_price"].astype(int)
    sold_pe_price = filter_ce["average_price"].astype(int)

    price_to_get_out_of_trade = (stop_loss + sold_ce_price + sold_pe_price).values[0]


    #print("Price to get out:"+ price_to_get_out_of_trade)

    while(True):
        current_ce_price = getCMP(bank_nifty_symbol_ce)
        current_pe_price = getCMP(bank_nifty_symbol_pe)
        if((current_ce_price + current_pe_price > price_to_get_out_of_trade) or end_time < now):
            logging.debug("Stoploss hit or time is up current ce price:"+ str(current_ce_price + current_pe_price)+ " and sl"+ str( price_to_get_out_of_trade))
            logging.debug("Stoploss hit or time is up current pe price:" + str(current_pe_price))
            logging.debug("end_time:" + str(end_time) + " now:" + str(now))
            #place_order(bank_nifty_symbol_ce, 0, lots, kite.TRANSACTION_TYPE_BUY, KiteConnect.EXCHANGE_NFO,
            #            KiteConnect.PRODUCT_MIS,KiteConnect.ORDER_TYPE_MARKET)
            #place_order(bank_nifty_symbol_pe, 0, lots, kite.TRANSACTION_TYPE_SELL, KiteConnect.EXCHANGE_NFO,
            #            KiteConnect.PRODUCT_MIS, KiteConnect.ORDER_TYPE_MARKET)
            break
        time.sleep(2)



if __name__ == '__main__':
    # Algo is place order by 175 at 9:20 with combined SL of 15 rs
    # Square of the strikes at 10:59 if SL not hit place new order at 11 for 175
    # Square of the strikes at 1:29 if SL not hit place new order at 1:30 for 175 strikes
    # square of the strikes at 2:59 if SL not hit and place new order at 3 for 175 strikes
    # Square of the strikes at 3:58
    # Find ATM Strike of Nifty
    NiftyATMStrike = getNearestStrikePrice(getCMP('NSE:NIFTY 50'))

    next_thursday_expiry = datetime.today() + relativedelta(weekday=TH(1))

    # nifty_symbol_ce = get_symbols(next_thursday_expiry.date(), 'NIFTY', NiftyATMStrike, 'CE')
    # nifty_symbol_pe = get_symbols(next_thursday_expiry.date(), 'NIFTY', NiftyATMStrike, 'PE')
    #

    logging.warning('This will get logged to a file')

    now = datetime.now()
    start_time = now.replace(hour=9, minute=20, second=0, microsecond=0)
    end_time = now.replace(hour=10, minute=59, second=0, microsecond=0)
    print("end_time:"+ str( end_time.time()))

    timeBasedStraddleSelling(start_time,end_time, 175, 15, 25)



    # pos_df = pd.DataFrame(kite.positions()["day"])
    # net_df = pos_df = pd.DataFrame(kite.positions()["net"])
    # print("day")
    # print(pos_df)
    # print("net")
    # print(net_df)
    #
    # #filter = pos_df["tradingsymbol"]=="NIFTY22MAR17800CE"
    #
    # data = pos_df[pos_df["tradingsymbol"]=="NIFTY22MAR17800CE"]
    #
    # print(data["average_price"])




