from kiteconnect import KiteConnect
from selenium import webdriver
from urllib.parse import urlparse, parse_qsl
import pandas as pd
import time
import os


cwd = os.chdir("/Users/padlakha/git/algo")

def autologin():
    token_path = "api_key.txt"
    key_secret = open(token_path,'r').read().split()
    kite = KiteConnect(api_key=key_secret[0])
    service = webdriver.chrome.service.Service('./chromedriver')
    service.start()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options = options.to_capabilities()
    driver = webdriver.Remote(service.service_url, options)
    driver.get(kite.login_url())
    driver.implicitly_wait(10)
    username = driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[1]/input')
    password = driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[2]/input')
    username.send_keys(key_secret[2])
    password.send_keys(key_secret[3])
    driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[4]/button').click()
    pin = driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[2]/div/input')
    pin.send_keys(key_secret[4])
    driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[3]/button').click()
    time.sleep(10)
    # request_token=driver.current_url.split('=')[1].split('&action')[0]
    parse_url = urlparse(driver.current_url)
    query_dict = dict(parse_qsl(parse_url.query))
    request_token=query_dict.get("request_token")
    with open('request_token.txt', 'w') as the_file:
        the_file.write(request_token)
    driver.quit()

autologin()

#generating and storing access token - valid till 6 am the next day
request_token = open("request_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
data = kite.generate_session(request_token, api_secret=key_secret[1])
with open('access_token.txt', 'w') as file:
        file.write(data["access_token"])
# instrument_dump = kite.instruments("NFO")
# instrument_df = pd.DataFrame(instrument_dump)
# instrument_df.to_csv("NFO_Instruments.csv",index=False)
instrument_dump = kite.instruments("NSE")
instrument_df = pd.DataFrame(instrument_dump)
instrument_df.to_csv("NSE_Instruments.csv",index=False)
#print(instrument_dump)
