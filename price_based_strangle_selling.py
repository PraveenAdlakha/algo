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
    current_strike = int(strike)

    if instrumentsList is None:
        instrumentsList = kite.instruments('NFO')

    for num in instrumentsList:
        if num['expiry'] == expiry and num['strike'] == current_strike and num['instrument_type'] == ins_type and num['name'] == name:
            if ins_type == "CE":
                current_strike = current_strike + 100
            if ins_type == "PE":
                current_strike = current_strike - 100
            if getCMP("NFO:"+ str(num['tradingsymbol'])) <= price:
                return num['tradingsymbol']


def getNearestPEStrikeByPrice(expiry, name, strike,ins_type , price):
    global instrumentsList
    atmStrike = strike
    current_strike = int(strike)

    if instrumentsList is None:
        instrumentsList = kite.instruments('NFO')
    df = pd.DataFrame(instrumentsList)
    df1 = df[(df.instrument_type == ins_type ) & (df.name == name) & (df.expiry == expiry)]
    if(ins_type == "PE"):
       df2 =  df1.sort_values(by=['strike'], ascending=False)
    if(ins_type == "CE"):
        df2 = df1.sort_values(by=['strike'], ascending=True)
    for row in df2.itertuples():
        if int(getCMP("NFO:"+ str(getattr(row,'tradingsymbol')))<= int(price)) and int((getattr(row,'strike'))< int(strike)):
            return getattr(row,'tradingsymbol')


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

        logging.debug('Order placed successfully, orderId = %s', orderId)
        return orderId
    except Exception as e:
        logging.debug('Order placement failed: %s', e.message)


def timeBasedStraddleSelling(start_time, end_time, price, stop_loss,target , qty):

    while (datetime.now() < start_time) :
        time.sleep(10)
        logging.debug("Wating for starttime:" + start_time.strftime("%m/%d/%Y, %H:%M:%S") + " right now its :  " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))


    if(datetime.now() > start_time and end_time > datetime.now()):
        BankNiftyATMStrike = getNearestStrikePrice(getCMP('NSE:NIFTY BANK'), 100)
        bank_nifty_symbol_ce = getNearestCEStrikeByPrice(next_thursday_expiry.date(), 'BANKNIFTY', BankNiftyATMStrike,
                                                         'CE',
                                                         price)
        bank_nifty_symbol_pe = getNearestPEStrikeByPrice(next_thursday_expiry.date(), 'BANKNIFTY', BankNiftyATMStrike,
                                                         'PE',price)
        logging.debug("Placing order for:" + str(bank_nifty_symbol_ce))
        logging.debug("Placing order for:" + str(bank_nifty_symbol_pe))


        place_order(bank_nifty_symbol_ce, 0, qty, kite.TRANSACTION_TYPE_SELL, KiteConnect.EXCHANGE_NFO, KiteConnect.PRODUCT_NRML,
                    KiteConnect.ORDER_TYPE_MARKET)

        place_order(bank_nifty_symbol_pe, 0, qty, kite.TRANSACTION_TYPE_SELL, KiteConnect.EXCHANGE_NFO, KiteConnect.PRODUCT_NRML,
                    KiteConnect.ORDER_TYPE_MARKET)
        ce_price = getCMP("NFO:"+bank_nifty_symbol_ce)
        pe_price = getCMP("NFO:"+bank_nifty_symbol_pe)
        time.sleep(5)

        monitorStrangleSold(end_time, bank_nifty_symbol_pe, bank_nifty_symbol_ce, stop_loss, qty, ce_price, pe_price, target)
    else:
        logging.debug("Current time is out of start and end time.")


def monitorStrangleSold(end_time, bank_nifty_symbol_pe, bank_nifty_symbol_ce, stop_loss, qty,ce_price ,pe_price, target):

    #pos_df = pd.DataFrame(kite.positions()["net"])
    #TODO change it to day net is for older position
    pos_df = pd.DataFrame(kite.positions()["day"])

    filter_pe = pos_df[pos_df["tradingsymbol"]== bank_nifty_symbol_pe]
    filter_ce = pos_df[pos_df["tradingsymbol"]== bank_nifty_symbol_ce]

    #sold_ce_price = filter_pe["average_price"].values[0]
    #sold_pe_price = filter_ce["average_price"].values[0]
    sold_ce_price = ce_price
    sold_pe_price = pe_price
#    price_to_get_out_of_trade = (stop_loss + sold_ce_price + sold_pe_price).values[0]

    price_to_get_out_of_trade = (stop_loss + sold_ce_price + sold_pe_price)
    #Trailing logic is after getting decay of 25 points move sl to cost.
    lowest = price_to_get_out_of_trade
    #print("Price to get out:"+ price_to_get_out_of_trade)

    while(True):
        try:
            #Trailing stoploss updation logic
            current_ce_price = getCMP("NFO:"+bank_nifty_symbol_ce)
            current_pe_price = getCMP("NFO:"+bank_nifty_symbol_pe)
            if((current_pe_price+current_ce_price + 25) < (sold_pe_price + sold_ce_price) ):
                lowest = sold_pe_price + sold_ce_price
            if(lowest < price_to_get_out_of_trade):
                price_to_get_out_of_trade = lowest
                logging.debug("new price to get out:"+ str(price_to_get_out_of_trade))
        except Exception as e:
            logging.debug('Exception in monitoring %s', e.message)
            pass
        if((current_ce_price + current_pe_price > price_to_get_out_of_trade) or end_time< datetime.now() or
                (current_pe_price + current_ce_price+ target) < (sold_pe_price+ sold_ce_price)):
            logging.debug("Stoploss hit or time is up current strangle price:"+ str(current_ce_price + current_pe_price)+ " and sl"+ str( price_to_get_out_of_trade))
            logging.debug("Current points:" + str(sold_ce_price+ sold_pe_price - current_pe_price- current_ce_price))
            logging.debug("end_time:" + str(end_time) + " now:" + str(now))
            place_order(bank_nifty_symbol_ce, 0, qty, kite.TRANSACTION_TYPE_BUY, KiteConnect.EXCHANGE_NFO,
                           KiteConnect.PRODUCT_NRML,KiteConnect.ORDER_TYPE_MARKET)
            place_order(bank_nifty_symbol_pe, 0, qty, kite.TRANSACTION_TYPE_BUY, KiteConnect.EXCHANGE_NFO,
                           KiteConnect.PRODUCT_NRML, KiteConnect.ORDER_TYPE_MARKET)
            break
            time.sleep(2)
        logging.debug("CMP: "+ str(current_ce_price+ current_pe_price)  + " and sl: " +  str( price_to_get_out_of_trade))



if __name__ == '__main__':
    # Algo is place order by 175 at 9:20 with combined SL of 15 rs
    # Square of the strikes at 10:59 if SL not hit place new order at 11 for 175
    # Square of the strikes at 1:29 if SL not hit place new order at 1:30 for 175 strikes
    # square of the strikes at 2:59 if SL not hit and place new order at 3 for 175 strikes
    # Square of the strikes at 3:58
    # Find ATM Strike of Nifty
    # NiftyATMStrike = getNearestStrikePrice(getCMP('NSE:NIFTY 50'))

    next_thursday_expiry = datetime.today() + relativedelta(weekday=TH(1))

    qty = 300
    now = datetime.now()
    target = 30
    stoploss = 15
    price_to_sell = 175
    # start_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
    # end_time = now.replace(hour=11, minute=25, second=0, microsecond=0)
    # print("end_time:"+ str( end_time.time()))
    #
    # timeBasedStraddleSelling(start_time, end_time, price_to_sell, stoploss, target, qty)

    start_time = now.replace(hour=11, minute=30, second=0, microsecond=0)
    end_time = now.replace(hour=13, minute=25, second=0, microsecond=0)
    print("end_time:"+ str( end_time.time()))

    timeBasedStraddleSelling(start_time, end_time, price_to_sell, stoploss, target, qty)

    start_time = now.replace(hour=13, minute=30, second=0, microsecond=0)
    end_time = now.replace(hour=14, minute=55, second=0, microsecond=0)
    print("end_time:"+ str( end_time.time()))

    timeBasedStraddleSelling(start_time, end_time, price_to_sell, stoploss, target, qty)

    # start_time = now.replace(hour=15, minute=0, second=0, microsecond=0)
    # end_time = now.replace(hour=15, minute=20, second=0, microsecond=0)
    # print("end_time:"+ str( end_time.time()))

    #timeBasedStraddleSelling(start_time, end_time, price_to_sell, stoploss, target, qty)

    #timeBasedStraddleSelling()

    #monitorStrangleSold(end_time, "BANKNIFTY2231034200CE", "BANKNIFTY2231033300PE", 15, qty, 163.36,191.9, 25)

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