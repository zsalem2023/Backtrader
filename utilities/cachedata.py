from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
import pandas

# https://interactivebrokers.github.io/tws-api/basic_contracts.html
import contracts

# https://interactivebrokers.github.io/tws-api/historical_bars.html
WTS = [
    'TRADES',
    'MIDPOINT',
    'BID',
    'ASK',
    'BID_ASK',
    'ADJUSTED_LAST',
    'HISTORICAL_VOLATILITY',
    'OPTION_IMPLIED_VOLATILITY',
    'REBATE_RATE',
    'FEE_RATE',
    'YIELD_BID',
    'YIELD_ASK',
    'YIELD_BID_ASK',
    'YIELD_LAST'
]

DURATIONS = [
    'S',
    'D',
    'W',
    'M',
    'Y'
]

VALID_BAR_SIZES = [
    '1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
    '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins', '20 mins', '30 mins',
    '1 hour', '2 hours', '3 hours', '4 hours', '8 hours', '1 day', '1 week', '1 month'
]

# modify parameters
end_date = '20200716 12:00:00 EST'  # yyyyMMdd hh:mm:ss {TMZ}
duration_value = 2                  # integer (duration value = amount of duration_unit)
duration_unit = DURATIONS[2]        # from  list (duration_unit = amount of data))
bar_size = VALID_BAR_SIZES[11]      # from list (intervals, bar sizes)
what_to_show = WTS[1]               # from list
contract, name = contracts.spy()    # from contracts.py
# end modify parameters

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = []

    def historicalData(self, reqId, bar):
        self.data.append([bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume])

def run_loop():
    app.run()

app = IBapi()
# app.connect('ec2-52-90-35-26.compute-1.amazonaws.com', 4002, 130)
app.connect('127.0.0.1', 4002, 130)
api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()
time.sleep(2)

app.reqHistoricalData(1, contract, end_date, str(duration_value)+' '+duration_unit, bar_size, what_to_show, 0, 2, False, [])
time.sleep(5) 
df = pandas.DataFrame(app.data, columns=['DateTime',"Open","High","Low", 'Close', 'Volume'])
df['DateTime'] = pandas.to_datetime(df['DateTime'],unit='s')
filename = 'data\\'+name+'-'+what_to_show+'-'+bar_size+'-bars-for-'+str(duration_value)+'-'+duration_unit+'-before-'+end_date+'.csv'
df.to_csv(filename.replace(' ', '-').replace(':', '-').lower())
app.disconnect()

