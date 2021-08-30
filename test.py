import time
import pyupbit
import datetime
import schedule
from fbprophet import Prophet

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=3)
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


# predict_price("KRW-IOTA")
# schedule.every().hour.do(lambda: predict_price("KRW-IOTA"))
krw_tickers = pyupbit.get_tickers(fiat="KRW")
total={}
test1=[]
for n in krw_tickers:
    target_price = get_target_price(n, 0.5)
    predict_price(n)
    #total[n]=predicted_close_price


    if target_price<=predicted_close_price:
        print(n,"타겟 가격 : ",target_price,"예상 종가 :",predicted_close_price)
        total[n]=target_price,predicted_close_price
print(total)





