from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt

import datetime as datetime
import logging
from backtrader.indicators import SimpleMovingAverage

# Disable debug logging for matplotlib
logging.getLogger('matplotlib').setLevel(logging.ERROR)


# Create a Stratey
class SMAStrategy(bt.Strategy):
    params = (
        ('small_sma_period', 5),
        ('medium_sma_period', 20),
        ('large_sma_period', 50),
        ('dolog', True)
    )

    def log(self, txt, dt=None, dolog=None, indent=False):
        dolog = dolog or self.p.dolog
        if dolog:
            dt = dt or self.datas[0].datetime.date(0)
            if indent: txt = "                      " + txt
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep references
        self.small = self.datas[0]
        self.large = self.datas[1]

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.pending_entry_order = False

        # Add a SMA indicator
        self.small_sma = SimpleMovingAverage(self.large, period=self.p.small_sma_period)
        self.medium_sma = SimpleMovingAverage(self.large, period=self.p.medium_sma_period)
        # self.large_sma = SimpleMovingAverage(self.large, period=self.p.large_sma_period)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if main order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

            else:
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.pending_entry_order = False

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def notify_data(self, data, status):
        if status == data.LIVE:
            print("DATA: Live")
        if status == data.CONNECTED:
            print("DATA: Connected")
        if status == data.DISCONNECTED:
            print("DATA: Disconnected")
        if status == data.CONNBROKEN:
            print("DATA: Connection Broken")
        if status == data.DELAYED:
            print("DATA: Delayed")

    def next(self):
        # Log the closing price of the seconds and minutes lines
        self.log('Small Close, %.2f' % self.small.close[0], dt=self.small.datetime.datetime(0))
        self.log('Large Close, %.2f' % self.large.close[0], dt=self.large.datetime.datetime(0), indent=True)


        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.pending_entry_order:
            return

        # Check if we are in the market
        if not self.position:

            # Buy if small SMA > medium SMA
            if self.small_sma[0] > self.medium_sma[0]:

                self.order = self.buy()
                self.pending_entry_order = True

            # Sell if price has dropped 5% or more in last 30 <small_time_period>
            elif self.small.close[-30] > self.small.close[0] * 1.0526:
                
                self.order = self.sell()
                self.pending_entry_order = True

if __name__ == '__main__':
    # Create cerebro        
    cerebro = bt.Cerebro()
    
    # Load data from IB into cerebro
    store = bt.stores.IBStore(host='127.0.0.1', port=7496, _debug=True)
    data = store.getdata(dataname='ES-202006-GLOBEX-USD',
                         #sectype='',
                         #exch='',
                         #curr='',
                         #expiry='',
                         #strike='',
                         #right='',
                         historical=True,
                         timeframe=bt.TimeFrame.Minutes,
                         compression=5,
                         fromdate=datetime.datetime(2020, 4, 22),
                         todate=datetime.datetime(2020, 5, 23)
    )
    
    # Add second data
    cerebro.adddata(data)              
    # Add minute data 
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Days, compression=1)
       
    # Add strategy to cerebro
    cerebro.addstrategy(SMAStrategy)
   
    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.plot(style='candlestick')