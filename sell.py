import time
import pyupbit
import datetime
import schedule
from fbprophet import Prophet

access = "Wb4hfzgxzGeDxhDB2xvxbR5guKE3eojuoL3VbxKB"
secret = "Hp6dRs1y7YFeqKzL8zMTb8JjpA10ePnMrovZHCXI"

upbit = pyupbit.Upbit(access, secret)
krw_tickers = pyupbit.get_tickers(fiat="KRW")
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

for n in krw_tickers:
    coin = get_balance(n[4:])
    if coin > 0.00008:
        upbit.sell_market_order(n,coin)
        print(n, "판매")