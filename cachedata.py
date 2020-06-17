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

BAR_SIZES = {
    'seconds': 'S',
    'days': 'D',
    'week': 'W',
    'month': 'M',
    'year', 'Y'
}

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
contract, name = contracts.spy()


#bids
app.reqHistoricalData(1, contract, '', '1 W', '1 hour', WTS[2], 0, 2, False, [])
time.sleep(5) 
df = pandas.DataFrame(app.bid_data, columns=['DateTime',"Open_Bid","High_Bid","Low_Bid", 'Close_Bid'])
print(df)
df['DateTime'] = pandas.to_datetime(df['DateTime'],unit='s') 
#asks
app.reqHistoricalData(2, contract, '', '1 W', '1 hour', 'ASK', 0, 2, False, [])
time.sleep(5)
df2 = pandas.DataFrame(app.ask_data, columns=['DateTime',"Open_Ask","High_Ask","Low_Ask", 'Close_Ask'])
print(df2)
df2['DateTime'] = pandas.to_datetime(df2['DateTime'],unit='s') 
df3 = df.merge(df2.set_index('DateTime'),on ='DateTime')
print(df3)
df3.to_csv('BID_ASK_'+name+'_Hourly.csv')  
app.disconnect()