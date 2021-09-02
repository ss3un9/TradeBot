import time
import pyupbit
import datetime
import schedule
from fbprophet import Prophet
import numpy as np

access = "Wb4hfzgxzGeDxhDB2xvxbR5guKE3eojuoL3VbxKB"
secret = "Hp6dRs1y7YFeqKzL8zMTb8JjpA10ePnMrovZHCXI"

upbit = pyupbit.Upbit(access, secret)
krw_tickers = pyupbit.get_tickers(fiat="KRW")

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

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


def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k

    return target_price


def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]


predicted_close_price = {}
def predict_price(ticker):
    """Prophet으로 당일 종가 가격 예측"""
    global predicted_close_price
    df = pyupbit.get_ohlcv(ticker, interval="minute15")
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
#predict_price("KRW-IOTA")
ma3={}
def get_ma3(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=3)
    ma3[ticker] = df['close'].rolling(3).mean().iloc[-1]


def predicted_price():
    for n in krw_tickers:
        predict_price(n)
        get_ma3(n)
        value_k(n)
        print(n,"종가 예측중 : ",predicted_close_price[n])
        print(n,"이동 평균선 조회중 :",ma3[n])
        print(n,"Best K값 : ",best_k[n])
best_k={}
def get_ror(ticker,k=0.5):
    df = pyupbit.get_ohlcv(ticker, count=7)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'],
                         1)

    ror = df['ror'].cumprod()[-2]
    return ror

def value_k(ticker):
    v1=0
    for k in np.arange(0.1, 1.0, 0.1):
        ror = get_ror(ticker,k)
        if v1<ror:
            v1=ror
            best_k[ticker]=k


predicted_price()
schedule.every().hour.do(predicted_price)
total=[]
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)
        schedule.run_pending()
        if start_time < now < end_time - datetime.timedelta(seconds=10):
            for n in krw_tickers:
                target_price = get_target_price(n,best_k[n])
                current_price = get_current_price(n)
                print(n,"target_price : ",target_price)
                print(n,"current_price: ",current_price)
                print(n,"predicted_close_price : " ,predicted_close_price[n])
                if target_price < current_price and current_price < predicted_close_price[n] and ma3[n] < current_price:
                    total.append(n)
                    print(total)

        else:
            for n in krw_tickers:
                coin = get_balance(n[:4])
                if coin > 0.00008:
                    upbit.sell_market_order("KRW-IOTA", coin*0.9995)
                    print("판매")
                else:
                    print("코인없음")

        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)




