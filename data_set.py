import time
import pyupbit
import datetime
import schedule
from fbprophet import Prophet
import numpy as np
import pandas

access = "Wb4hfzgxzGeDxhDB2xvxbR5guKE3eojuoL3VbxKB"
secret = "Hp6dRs1y7YFeqKzL8zMTb8JjpA10ePnMrovZHCXI"

upbit = pyupbit.Upbit(access, secret)
krw_tickers = pyupbit.get_tickers(fiat="KRW")

def trading():
    global count
    for n in krw_tickers:

        data = pyupbit.get_ohlcv(ticker=n, interval="minute3")

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute60", count=2)
    print(df)
    start_time = df.index[0]
    print(start_time)
    return start_time
get_start_time("KRW-BTC")
def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute3", count=81)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k

    return target_price
predicted_close_price = {}
def predict_price(ticker):
    """Prophet으로 당일 종가 가격 예측"""
    global predicted_close_price
    df = pyupbit.get_ohlcv(ticker, interval="minute60")
    df = df.reset_index()
    df['ds'] = df['index']
    df['y'] = df['close']
    data = df[['ds','y']]
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=24, freq='H')
    forecast = model.predict(future)
    closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=9)]
    if len(closeDf) == 0:
        closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=9)]
    closeValue = closeDf['yhat'].values[0]
    predicted_close_price[ticker] = closeValue

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:

        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0
def sell():
    a=0
    for n in krw_tickers:  # for n in buy_list로 변경
        coin = get_balance(n[4:])

        if coin > 0.0008:
            a+=1
            print(n,a)
            avg=upbit.get_avg_buy_price(n)
            now=get_current_price(n)
            if avg*1.05<=now<=avg*1.1:
                print(n,"절반만 팜")
            elif avg<=now<avg*1.05:
                print(n,"팜")

            elif now*1.01<avg<now*1.05:
                print(n,"존버")
            else:
                print(n,"머지")
















#3,90 : 73707000.0
#15,12 : 73469000.0

#df = pyupbit.get_ohlcv("KRW-BTC", interval="minute3", count=90)
#print(df)



