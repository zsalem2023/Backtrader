from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
import pandas

# https://interactivebrokers.github.io/tws-api/basic_contracts.html
import contracts

# https://interactivebrokers.github.io/tws-api/historical_bars.html
WTS = 'bids and asks combined'

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
end_date = '20200616 12:00:00 EST'  # yyyyMMdd hh:mm:ss {TMZ}
duration_value = 1                  # integer
duration_unit = DURATIONS[3]        # from list
bar_size = VALID_BAR_SIZES[13]      # from list
contract, name = contracts.spy()    # from contracts.py
# end modify parameters

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.bid_data = [] #Initialize variable to store bid candle
        self.ask_data = [] #Initialize variable to store ask candle

    def historicalData(self, reqId, bar):
        print(f'Time: {bar.date} Open: {bar.open} Close: {bar.close}')
        if (reqId == 1):
            self.bid_data.append([bar.date, bar.open, bar.high, bar.low, bar.close])
        else:
            self.ask_data.append([bar.date, bar.open, bar.high, bar.low, bar.close])

def run_loop():
    app.run()

app = IBapi()
app.connect('127.0.0.1', 4001, 130)
api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()
time.sleep(2) #Sleep interval to allow time for connection to server

#bids
app.reqHistoricalData(1, contract, end_date, str(duration_value)+' '+duration_unit, bar_size, 'BIDS', 0, 2, False, [])
time.sleep(5) 
df = pandas.DataFrame(app.bid_data, columns=['DateTime',"Open_Bid","High_Bid","Low_Bid", 'Close_Bid'])
print(df)
df['DateTime'] = pandas.to_datetime(df['DateTime'],unit='s')
#asks
app.reqHistoricalData(2, contract, end_date, str(duration_value)+' '+duration_unit, bar_size, 'ASK', 0, 2, False, [])
time.sleep(5)
df2 = pandas.DataFrame(app.ask_data, columns=['DateTime',"Open_Ask","High_Ask","Low_Ask", 'Close_Ask'])
print(df2)
df2['DateTime'] = pandas.to_datetime(df2['DateTime'],unit='s')
df3 = df.merge(df2.set_index('DateTime'),on ='DateTime')
print(df3)
filename = 'data/BID ASK '+name+' '+bar_size+' bars for '+str(duration_value)+' '+duration_unit+' before '+end_date+'.csv'
df3.to_csv(filename)
app.disconnect()