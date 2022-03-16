import logging
import os
from datetime import datetime
import pandas as pd

from dateutil.relativedelta import relativedelta, TH
from kiteconnect import KiteConnect
import time

cwd = os.chdir("/Users/padlakha/git/algo")

#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)
logging.basicConfig(filename='./logs/sellAndMonitorStraddle.log', filemode='a', format='%(asctime)s - %(message)s',level=logging.DEBUG)


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

def sellAndMonitorStraddle(bank_nifty_symbol_ce,bank_nifty_symbol_pe, sell_price, stoploss, qty, target):
    ce_current_price = getCMP("NFO:"+bank_nifty_symbol_ce)
    pe_current_price = getCMP("NFO:"+ bank_nifty_symbol_pe)

    while(True):
        if(ce_current_price + pe_current_price < sell_price):
            place_order(bank_nifty_symbol_ce, 0, qty, kite.TRANSACTION_TYPE_SELL, KiteConnect.EXCHANGE_NFO,
                        KiteConnect.PRODUCT_NRML,
                        KiteConnect.ORDER_TYPE_MARKET)

            place_order(bank_nifty_symbol_pe, 0, qty, kite.TRANSACTION_TYPE_SELL, KiteConnect.EXCHANGE_NFO,
                        KiteConnect.PRODUCT_NRML,
                        KiteConnect.ORDER_TYPE_MARKET)
            break
        time.sleep(3)

    monitorSoldStrike(bank_nifty_symbol_pe,bank_nifty_symbol_ce, ce_current_price, pe_current_price, stoploss, qty, target)


def monitorSoldStrike(bank_nifty_symbol_pe,bank_nifty_symbol_ce, ce_sold_price, pe_sold_price, stoploss, qty, target):

    while(True):
        ce_current_price = getCMP("NFO:" + bank_nifty_symbol_ce)
        pe_current_price = getCMP("NFO:" + bank_nifty_symbol_pe)

        if(ce_current_price+ pe_current_price > ce_sold_price + pe_sold_price + stoploss):
            logging.debug("SL hit getting out.")
            place_order(bank_nifty_symbol_ce, 0, qty, kite.TRANSACTION_TYPE_BUY, KiteConnect.EXCHANGE_NFO,
                        KiteConnect.PRODUCT_NRML, KiteConnect.ORDER_TYPE_MARKET)
            place_order(bank_nifty_symbol_pe, 0, qty, kite.TRANSACTION_TYPE_BUY, KiteConnect.EXCHANGE_NFO,
                        KiteConnect.PRODUCT_NRML, KiteConnect.ORDER_TYPE_MARKET)
            break
        logging.debug("Monitoring cmp :"+ str(ce_current_price+ pe_current_price) + " Profit:"+ str(pe_sold_price+ ce_sold_price-ce_current_price- pe_current_price))

        if(ce_current_price+ pe_current_price+ target < ce_sold_price + pe_sold_price ):
            logging.debug("target hit, getting out CMP:"+ str(ce_current_price+ pe_current_price+ target))
            place_order(bank_nifty_symbol_ce, 0, qty, kite.TRANSACTION_TYPE_BUY, KiteConnect.EXCHANGE_NFO,
                        KiteConnect.PRODUCT_NRML, KiteConnect.ORDER_TYPE_MARKET)
            place_order(bank_nifty_symbol_pe, 0, qty, kite.TRANSACTION_TYPE_BUY, KiteConnect.EXCHANGE_NFO,
                        KiteConnect.PRODUCT_NRML, KiteConnect.ORDER_TYPE_MARKET)
            break








if __name__ == '__main__':
    bank_nifty_symbol_ce = "BANKNIFTY2231735400CE"
    bank_nifty_symbol_pe = "BANKNIFTY2231735400PE"
    sell_price = 1150
    stoploss = 0
    qty = 25
    target = 100
    #sellAndMonitorStraddle(bank_nifty_symbol_ce,bank_nifty_symbol_pe, sell_price, stoploss, qty, target)

    monitorSoldStrike(bank_nifty_symbol_pe,bank_nifty_symbol_ce, 504.30 ,625.10 , stoploss, qty, target)