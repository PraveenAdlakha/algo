# # -*- coding: utf-8 -*-
# """
# Connecting to KiteConnect API
#
# """
#
# from kiteconnect import KiteConnect
# import pandas as pd
#
# api_key = "it15m9stiwi3pth5"
# api_secret = "fn26di9ko32okghogjywmg6hkfrjtyaz"
# kite = KiteConnect(api_key=api_key)
# print(kite.login_url()) #use this url to manually login and authorize yourself
#
# #generate trading session
# request_token = "C6z2iToIeAXA3W2h3En3YVCZ2m5WXSp6" #Extract request token from the redirect url obtained after you authorize yourself by loggin in
# data = kite.generate_session(request_token, api_secret=api_secret)
#
# #create kite trading object
# kite.set_access_token(data["access_token"])
#
#
# instrument_dump = kite.instruments("NSE")
# instrument_df = pd.DataFrame(instrument_dump)
# instrument_df.to_csv("NSE_Instruments.csv",index=False)