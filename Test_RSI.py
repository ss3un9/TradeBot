import time
import pyupbit
import datetime
import schedule
from fbprophet import Prophet
import numpy as np
import pandas
import csv
from bs4 import BeautifulSoup
import requests
import threading


""" API 키"""
access = ""
secret = ""
upbit = pyupbit.Upbit(access, secret)


"""코인 가져오기"""
#krw_tickers = pyupbit.get_tickers(fiat="KRW")
krw_tickers2 = ['KRW-SAND', 'KRW-HUM', 'KRW-MANA', 'KRW-CRO', 'KRW-FLOW', 'KRW-BORA', 'KRW-XRP', 'KRW-POWR', 'KRW-STPT', 'KRW-ICX', 'KRW-CVC', 'KRW-IOTA', 'KRW-WAXP', 'KRW-MOC', 'KRW-STX', 'KRW-AERGO', 'KRW-STORJ', 'KRW-ENJ', 'KRW-LOOM', 'KRW-MLK', 'KRW-HIVE', 'KRW-TRX', 'KRW-ATOM', 'KRW-QTUM', 'KRW-ETC', 'KRW-META']



"""코인 제거"""
#krw_tickers.remove("KRW-1INCH")
#krw_tickers.remove("KRW-AAVE")
#krw_tickers2.remove("KRW-ALGO")
#krw_tickers2.remove("KRW-BTC")
#krw_tickers2.remove("KRW-ETH")

""" 코인이름 포맷 """
bug2 = dict.fromkeys(krw_tickers2)
bug = {}            # TOP 20 거래대금 가져오기
bug3= {}


"""변수 리스트"""
tickers= []         # 현재 거래대금 탑 20
buy_count = 0       # 사는 코인 갯수 (제한 : 3개)
buy_coin_name= [0,0,0]   # 사는 코인 이름 저장
buy_coin_price= [0,0,0]  # 사는 코인 가격 저장
my_price= 0;


"""현재가 조회"""
def get_current_price(ticker):
    return pyupbit.get_current_price(ticker)


""" 거래대금 TOP20 가져오기 """
def top20():
    tickers.clear()
    url = "https://www.coingecko.com/ko/거래소/upbit"
    bs = BeautifulSoup(requests.get(url).text,'html.parser')
    ticker_temp = bs.find_all("a", attrs={"rel":"nofollow noopener", "class":"mr-1"})
    for i in range(20):
        tickers.append('KRW-' + list(ticker_temp[i])[0][1:-5])
    tickers.remove("KRW-BTC")
    tickers.remove("KRW-ETH")
    print(tickers)
    bug = dict.fromkeys((tickers))



""" 잔고 조회 """
def get_balance(ticker):
    balances = upbit.get_balances()
    for b in balances:

        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0


""" RSI 계산 """
def rsi(ohlc: pandas.DataFrame, period: int = 14):
    delta = ohlc["close"].diff()
    ups, downs = delta.copy(), delta.copy()
    ups[ups < 0] = 0
    downs[downs > 0] = 0
    AU = ups.ewm(com = period-1, min_periods = period).mean()
    AD = downs.abs().ewm(com = period-1, min_periods = period).mean()
    RS = AU/AD
    return pandas.Series(100 - (100/(1 + RS)), name = "RSI")


""" RSI 저장 """
def rsi_cal2():
    global buy_count

    if buy_count < 3:
        for i in range(len(krw_tickers2)):
            data = pyupbit.get_ohlcv(ticker=krw_tickers2[i], interval="minute1")
            now_rsi = rsi(data,14).iloc[-1]

            time.sleep(0.1)
            #bug3[tickers[i]]=now_rsi  #없어도 됨

            bug[krw_tickers2[i]]=now_rsi

            if bug[krw_tickers2[i]] > 40:
                bug.pop(krw_tickers2[i])
        print("**********************************************")
        print("초기 값:", bug)
        print("**********************************************")


""" 실시간 RSI 분석 """
def rsi_cal3():
    global buy_count
    if buy_count < 3:
        for key, value in bug.items():
            data = pyupbit.get_ohlcv(ticker=key, interval="minute1")
            now_rsi = rsi(data,14).iloc[-1]
            time.sleep(0.5)
            bug3[key] = now_rsi


            if value+10 < now_rsi:
                buy(key)

        print("--------------------------------------------")
        print("--------------------------------------------")
        print("초기:", bug)
        print("현재:", bug3)


""" 코인 사기 """
def buy(coin):
    global buy_count
    krw = get_balance("KRW")


    if money >= 5005:
        upbit.buy_market_order(coin, money*0.9995)
        time.sleep(1)
        buy_count += 1
        for i in range(0,len(buy_coin_name)):
            if buy_coin_name[i] == 0:
                buy_coin_name[i] = coin
                print("구매 코인: ",buy_coin_name)


""" 코인 분석 및 팔기 """
def sell_cal():
    global buy_count
    if buy_count > 0:
        for i in range(0, len(buy_coin_name)):
            if buy_coin_name[i] != 0:
                current_price = get_current_price(buy_coin_name[i])
                if buy_coin_price[i] == 0:
                    buy_coin_price[i] = current_price

                elif buy_coin_price[i] < current_price :
                    upbit.sell_market_order(buy_coin_name[i], get_balance(buy_coin_name[i]))
                    buy_coin_price[i]=0
                    buy_coin_name[i]=0
                    buy_count -= 1
                    print("판매코인 :", buy_coin_name[i])



schedule.every(30).seconds.do(rsi_cal2)
schedule.every(10).seconds.do(sell_cal)

while True:
    try:
        schedule.run_pending()
        rsi_cal3()
        time.sleep(0.1)

    except Exception as e:
        print(e)
        time.sleep(0.5)