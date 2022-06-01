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

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute240", count=1)
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
    df = pyupbit.get_ohlcv(ticker, interval="minute3", count=81) #minute15 , count12 에서 변경
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k

    return target_price


def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]


predicted_close_price = {}
def predict_price(ticker):
    """Prophet으로 당일 종가 가격 예측"""
    global predicted_close_price
    df = pyupbit.get_ohlcv(ticker, interval="minute3",count=81)
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
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma3[ticker] = df['close'].rolling(15).mean().iloc[-1]


def predicted_price():
    for n in krw_tickers:
        predict_price(n)
        time.sleep(0.5)
        get_ma3(n)
        time.sleep(0.5)
        value_k(n)
        time.sleep(0.5)
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
buy_list=[]
count=0

def rsi(ohlc: pandas.DataFrame, period: int = 14):
    delta = ohlc["close"].diff()
    ups, downs = delta.copy(), delta.copy()
    ups[ups < 0] = 0
    downs[downs > 0] = 0
    AU = ups.ewm(com = period-1, min_periods = period).mean()
    AD = downs.abs().ewm(com = period-1, min_periods = period).mean()
    RS = AU/AD
    return pandas.Series(100 - (100/(1 + RS)), name = "RSI")

def trading():
    global count
    for n in krw_tickers:

        data = pyupbit.get_ohlcv(ticker=n, interval="minute3")
        now_rsi = rsi(data, 14).iloc[-1]

        target_price = get_target_price(n, best_k[n])
        current_price = get_current_price(n)
        print(n, "target_price : ", target_price)
        print(n, "current_price: ", current_price)
        print(n, "predicted_close_price : ", predicted_close_price[n])
        #print(n,"RSI 값 : ",now_rsi)
        print("**********Finding**********")
        print()
        print("현재시간 : ",now)
        if now>end_time:
            break

        if (target_price< current_price <= target_price * 1.05) and (ma3[n] < current_price < predicted_close_price[n]):
            if n not in buy_list:
                buy_list.append(n)
                print("**********FIND!!**********")
                print("Buy_list : ",buy_list)
                print("**************************")
                print()
                buy(n)






"""            krw = get_balance("KRW")
            if krw > 6000:  # if krw/len(buy_list) < 5100
                upbit.buy_market_order(n, 6000) # upbit.buy_market_order(n,krw/len(buy_list))
                print(n, " ****구매*****")
            if krw<6000: # 5000
                count+=1
                break"""
def buy(ticker):
    krw = get_balance("KRW")
    rate=krw/len(buy_list)
    print("남은 원화 : ", krw)
    global count
    if count<1:

        if krw < 20000:  # if krw/len(buy_list) < 5100
            upbit.buy_market_order(ticker, krw * 0.9995)  # upbit.buy_market_order(n,krw/len(buy_list))
            print(ticker, "=======구매=========")
            print("=======구매 금액 =========")
            print(krw)
            print("==========================")
            count += 1
        elif krw < 50000:  # if krw/len(buy_list) < 5100
            upbit.buy_market_order(ticker, krw * 0.4)  # upbit.buy_market_order(n,krw/len(buy_list))
            print(ticker, "=======구매=========")
            print("=======구매 금액 =========")
            print(krw * 0.4)
            print("==========================")
        elif krw < 100000:
            upbit.buy_market_order(ticker, krw * 0.25)  # upbit.buy_market_order(n,krw/len(buy_list))
            print(ticker, "=======구매=========")
            print("=======구매 금액 =========")
            print(krw * 0.25)
            print("==========================")
        elif krw < 250000:
            upbit.buy_market_order(ticker, krw * 0.1)  # upbit.buy_market_order(n,krw/len(buy_list))
            print(ticker, "=======구매=========")
            print("=======구매 금액 =========")
            print(krw * 0.1)
            print("==========================")
        elif krw < 500000:
            upbit.buy_market_order(ticker, krw * 0.05)  # upbit.buy_market_order(n,krw/len(buy_list))
            print(ticker, "=======구매=========")
            print("=======구매 금액 =========")
            print(krw * 0.05)
            print("==========================")






# start_time = get_start_time("KRW-BTC")
# now = datetime.datetime.now()
#
# end_time = start_time + datetime.timedelta(minutes=180)- datetime.timedelta(seconds=5)
#
# print("현재시간",now)
# print("Start_time : ",start_time)
# print("end_time : ",end_time)





predicted_price()
#schedule.every(3).hours.do(lambda: predicted_price())
while True:
    try:
        #print("try 부분 스케쥴 팬딩")
        #schedule.run_pending()
        time.sleep(1)
        start_time = get_start_time("KRW-BTC")
        now = datetime.datetime.now()

        end_time = start_time + datetime.timedelta(minutes=240)- datetime.timedelta(seconds=5)

        print("현재시간",now)
        print("Start_time : ",start_time)
        print("end_time : ",end_time)
        print("Buy_List : ",buy_list)
        print("Count = ",count)# count 수 추가
        time.sleep(1)
        if start_time < now < end_time - datetime.timedelta(seconds=10):

            while count<1:
                now = datetime.datetime.now()
                time.sleep(1)
                trading()
                if now>end_time:
                    break

        elif now > end_time:
            count=0
            for n in krw_tickers: # for n in buy_list로 변경
                coin = get_balance(n[4:])
                if coin > 0.00008:
                    upbit.sell_market_order(n, coin)
                    print(n,"판매")
            buy_list.clear()
            predicted_price()
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)


