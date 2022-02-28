import logging
import os
from datetime import datetime
import pandas as pd

from dateutil.relativedelta import relativedelta, TH
from kiteconnect import KiteConnect
import time

now = datetime.now()
start_time = now.replace(hour=12, minute=20, second=0, microsecond=0)
end_time = now.replace(hour=14, minute=59, second=0, microsecond=0)
print("end_time:" + str(end_time.time()))

print(end_time<now)
