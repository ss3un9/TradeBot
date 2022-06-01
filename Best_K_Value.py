import time
import pyupbit
import datetime
import schedule
from fbprophet import Prophet
import numpy as np

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k

    return target_price


predicted_close_price = 0
def predict_price(ticker):
    """Prophet으로 당일 종가 가격 예측"""
    global predicted_close_price
    df = pyupbit.get_ohlcv(ticker, interval="minute15")
    df = df.reset_index()
    df['ds'] = df['index']
    df['y'] = df['close']
    data = df[['ds', 'y']]
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=24, freq='H')
    forecast = model.predict(future)
    closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=9)]
    if len(closeDf) == 0:
        closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=9)]
    closeValue = closeDf['yhat'].values[0]
    predicted_close_price = closeValue

def get_ror(ticker,k=0.5):
    df = pyupbit.get_ohlcv(ticker, count=7)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'],
                         1)

    ror = df['ror'].cumprod()[-2]
    return ror



v1=0


# predict_price("KRW-IOTA")
# schedule.every().hour.do(lambda: predict_price("KRW-IOTA"))
krw_tickers = pyupbit.get_tickers(fiat="KRW")
total={}
v1=0
for n in krw_tickers:
    current_price=get_current_price(n)
    for k in np.arange(0.1, 1.0, 0.1):
        ror = get_ror(n,k)

        if v1<ror:
            v1=ror
            print(v1)
            max_k=k
    print(n, "MAX K 값: ",max_k)
    target_price=get_target_price(n,max_k)
    predict_price(n)
    ai_price=predicted_close_price
    if target_price < current_price and current_price < predicted_close_price:
        total[n]=target_price,ai_price
        print("적합 코인 : ",n)

print(total)
