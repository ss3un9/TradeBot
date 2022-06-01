import time
import pyupbit
import datetime
import schedule
from fbprophet import Prophet
import numpy as np
def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute240",count=1)
    start_time = df.index[0]
    return start_time

start_time = get_start_time("KRW-BTC")
now = datetime.datetime.now()
end_time = start_time + datetime.timedelta(minutes=60)- datetime.timedelta(seconds=5)


print(start_time)
print(now)
print(end_time)