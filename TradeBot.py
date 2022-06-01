import time
import pyupbit
import datetime
import schedule
from fbprophet import Prophet
import numpy as np
import pandas
from bs4 import BeautifulSoup
import requests
from openpyxl import load_workbook
access = "access API"
secret = "secret API"
upbit = pyupbit.Upbit(access, secret)
krw_tickers = pyupbit.get_tickers(fiat="KRW")
#krw_tickers.remove("KRW-ALGO")
#krw_tickers.remove("KRW-AAVE")

buy_list=[]
count=0
predicted_close_price = {}
ma3={}
best_k={}
#top_tickers=["KRW-THETA","KRW-CHZ","KRW-AXS","KRW-MANA","KRW-ENJ","KRW-FLOW","KRW-BORA","KRW-SSX","KRW-MOC","KRW-PLA","KRW-IOST","KRW-LINK","KRW-SAND","KRW-HIVE","KRW-STORJ","KRW-SNT"]



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
    df = pyupbit.get_ohlcv(ticker, interval="minute60", count=12)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k

    return target_price


def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]


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

def get_ma3(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma3[ticker] = df['close'].rolling(15).mean().iloc[-1]

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


def predicted_price():
    for n in krw_tickers:
        predict_price(n)
        time.sleep(0.2)
        get_ma3(n)
        time.sleep(0.2)
        value_k(n)
        time.sleep(0.2)
        print(n,"종가 예측중 : ",predicted_close_price[n])
        print(n,"이동 평균선 조회중 :",ma3[n])
        print(n,"Best K값 : ",best_k[n])



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


        target_price = get_target_price(n, best_k[n])
        current_price = get_current_price(n)
        data = pyupbit.get_ohlcv(ticker=n, interval="minute3")
        now_rsi = rsi(data, 14).iloc[-1]
        print("*********Finding Coin***********")



        if (target_price< current_price <= target_price * 1.03) and (ma3[n] < current_price < predicted_close_price[n]) and 23<=now_rsi<=50:
            if n not in buy_list:
                buy_list.append(n)
                print("FIND COIN ! : ", n)

    buy()

def buy():
    krw = get_balance("KRW")
    count_coin=len(buy_list)
    rate=krw/count_coin
    global count
    print("남은 원화 : ", krw)
    if count<1 and 500000<krw and count_coin <=1:

        for n in buy_list:
            coin = get_balance(n[4:])
            if coin <= 0.00008:
                upbit.buy_market_order(n, 500000)  # upbit.buy_market_order(n,krw/len(buy_list))
                time.sleep(1)

    elif count<1 and rate >= 5005:
        for n in buy_list:
            upbit.buy_market_order(n, rate * 0.9995)  # upbit.buy_market_order(n,krw/len(buy_list))
            time.sleep(1)
        count+=1
        buy_list.clear()
    else:
        count += 1
        buy_list.clear()







def sell():
    global count

    for n in krw_tickers:  # for n in buy_list로 변경
        coin = get_balance(n[4:])

        if coin > 0.00008:
            avg=upbit.get_avg_buy_price(n)
            now=get_current_price(n)

            if avg*1.02<=now<=avg*1.09: #2프로 이상 9프로 사이
                upbit.sell_market_order(n, coin)
                count=0

                print(n,"모두 판매 (익절)")

            if avg*1.1<now<avg*1.2: #10~ 20프로 이상
                if coin * 0.3 * now > 100000:
                    upbit.sell_market_order(n, coin*0.3)
                    count = 0
                    print(n,"30% 판매 (익절)")
                else:
                    upbit.sell_market_order(n,coin)
                    count = 0
                    print(n ,"모두 판매 (익절)")




            if avg*0.93<=now<=avg*0.97: # 4프로 ~ 7프로 손절
                if coin * 0.5 * now > 100000:
                    upbit.sell_market_order(n, coin*0.5)
                    count = 0
                    print(n, "50프로 판매 (손절)")
                else:
                    upbit.sell_market_order(n,coin)
                    count = 0
                print(n,"판매 (손절)")
    buy_list.clear()
    predicted_price()


def rsi_sell():
    global count
    print("*******************")
    print("*10마다 RSI 체크*")
    print("*******************")
    for n in krw_tickers:
        coin = get_balance(n[4:])
        if coin > 0.00008:
            avg = upbit.get_avg_buy_price(n)
            now = get_current_price(n)
            data = pyupbit.get_ohlcv(ticker=n, interval="minute3")
            now_rsi = rsi(data, 14).iloc[-1]
            if now_rsi>=72:
                if avg * 1.03 <= now:
                    if coin * 0.5 * now > 200000:
                        upbit.sell_market_order(n, coin * 0.3)
                        print("RSI 참고 절반 익절판매")
                        count=0
                        predicted_price()
                    else:
                        upbit.sell_market_order(n,coin)
                        print("RSI 참고 판매")
                        count=0
                        predicted_price()
            if avg*0.93<=now<=avg*0.97: # 4프로 ~ 7프로 손절
                if coin * 0.5 * now > 100000:
                    upbit.sell_market_order(n, coin*0.5)
                    count = 0
                    print(n, "50프로 판매 (손절)")
                else:
                    upbit.sell_market_order(n,coin)
                    count = 0
                print(n,"판매 (손절)")


def save():
    result=0
    krw = get_balance("KRW")
    result+=krw
    for n in krw_tickers:
        coin = get_balance(n[4:])
        if coin > 0:
            now=get_current_price(n)
            result+=now*coin
    wb = load_workbook("현황.xlsx")
    sheet=wb.active
    time = datetime.datetime.now()
    data_write=[time,result]
    sheet.append(data_write)
    wb.save("현황.xlsx")

coin_balance=[]
def my_coin_balance():
    coin_balance.clear()

    for n in krw_tickers:  # for n in buy_list로 변경
        coin = get_balance(n[4:])
        if coin > 0:
            coin_balance.append(n)


krw=get_balance("KRW")
if krw<100000:
    count+=1
else:
    predicted_price()

schedule.every().hour.at(":00").do(save)


#schedule.every().hour.at(":00").do(predicted_price)
schedule.every(10).minutes.do(rsi_sell)# 10분마다 실행
schedule.every(10).minutes.do(my_coin_balance)

while True:
    try:
        #print("try 부분 스케쥴 팬딩")
        schedule.run_pending()
        time.sleep(0.2)
        start_time = get_start_time("KRW-BTC")
        now = datetime.datetime.now()

        end_time = start_time + datetime.timedelta(minutes=240)- datetime.timedelta(seconds=5)
        print("")

        print("현재 시간 : ",now)
        print("구매 시간 : ",start_time)
        print("판매 시간 : ",end_time)
        print("count : ",count)
        print("coin_list : ",coin_balance)
        time.sleep(1)
        if start_time < now < end_time - datetime.timedelta(seconds=10):
            krw = get_balance("KRW")

            while count<1:
                now = datetime.datetime.now()
                time.sleep(0.2)
                #predicted_price()
                trading()
                if now>end_time:
                    break

        elif now > end_time - datetime.timedelta(seconds=10):

            sell()


        time.sleep(0.2)
    except Exception as e:
        print(e)
        time.sleep(0.5)


