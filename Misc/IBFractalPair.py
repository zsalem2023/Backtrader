from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt

import datetime as datetime
import logging
import FractalIndicators as FI
from backtrader.indicators import (EMA, MACD, Stochastic)

# Disable debug logging for matplotlib
logging.getLogger('matplotlib').setLevel(logging.ERROR)


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('fractal_period', 5),
        ('profit_percent', 10), # input hundreths of one percent 
        ('loss_percent', 10),   # input hundreths of one percent 
        ('tick_size', 0.25),
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
        self.secondsA = self.datas[0]
        self.minutesA = self.datas[1]
        self.secondsB = self.datas[2]
        self.minutesB = self.datas[3]

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.pending_entry_order = False

        # Add Fractal Difference indicators
        self.fractal_diff_a = FI.FractalDiff(
            self.minutesA, period=self.p.fractal_period, mult=5, plotname='A Diff'
        )
        self.fractal_diff_b = FI.FractalDiff(
            self.minutesB, period=self.p.fractal_period, mult=1, plotname='B Diff'
        )

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
        self.log('Minutes A Close, %.2f' % self.minutesA.close[0], dt=self.minutesA.datetime.datetime(0))
        self.log('Seconds A Close, %.2f' % self.secondsA.close[0], dt=self.secondsA.datetime.datetime(0), indent=True)
        self.log('Minutes B Close, %.2f' % self.minutesB.close[0], dt=self.minutesB.datetime.datetime(0))
        self.log('Seconds B Close, %.2f' % self.secondsB.close[0], dt=self.secondsB.datetime.datetime(0), indent=True)
    

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.pending_entry_order:
            return

        # Check if we are in the market
        if not self.position:

            # Buy if broke above up last up fractal
            if self.fractal_diff_a.l.up_diff[0] - self.fractal_diff_b.l.up_diff[0] > 30:

                self.log('SELL A & BUY B | Diff: {}'.format(
                    self.fractal_diff_a.l.up_diff[0] - self.fractal_diff_b.l.up_diff[0]))

                self.order = self.sell(data=self.secondsA)
                self.order = self.buy(data=self.secondsB)
                self.pending_entry_order = True

            # Sell if broke below last down fractal
            elif self.fractal_diff_b.l.up_diff[0] - self.fractal_diff_a.l.up_diff[0] > 30:
                
                entry_price = seconds_high - 0.50
                profit_taker = entry_price * (1 - self.p.profit_percent / 10000)
                stop_loss = entry_price * (1 + self.p.loss_percent / 10000)

                self.log('SELL BRACKET | CREATE: {}  PROFIT TAKER: {}  STOP LOSS: {}'.format(entry_price, profit_taker, stop_loss))

                self.fractal.last_fractals['down'] = 0

                # Keep track of the created order to avoid a 2nd order
                stopinfo = {'price': stop_loss,
                            'pricelimit': stop_loss + self.p.tick_size,
                            'exectype': bt.Order.StopLimit}
                self.order = self.sell_bracket(price = entry_price, limitprice=profit_taker, stopargs=stopinfo)
                self.pending_entry_order = True

if __name__ == '__main__':
    #Create cerebro        
    cerebro = bt.Cerebro()

    #load data from IB into cerebro
    store = bt.stores.IBStore(host='127.0.0.1', port=7497, _debug=True)
    
    dataA = store.getdata(name='A',
                         dataname='ES-202006-GLOBEX-USD',
                         #sectype='',
                         #exch='',
                         #curr='',
                         #expiry='',
                         #strike='',
                         #right='',
                         historical=True,
                         timeframe=bt.TimeFrame.Seconds,
                         compression=5,
                         fromdate=datetime.datetime(2020, 4, 16, 12),
                         todate=datetime.datetime(2020, 4, 16, 14)
    )
    dataB = store.getdata(name='B',
                         dataname='YM-202006-GLOBEX-USD',
                         #sectype='',
                         #exch='',
                         #curr='',
                         #expiry='',
                         #strike='',
                         #right='',
                         historical=True,
                         timeframe=bt.TimeFrame.Seconds,
                         compression=5,
                         fromdate=datetime.datetime(2020, 4, 16, 12),
                         todate=datetime.datetime(2020, 4, 16, 14)
    )
    # Add A second data
    cerebro.adddata(dataA)                     
    # Add A minute data 
    cerebro.resampledata(dataA, timeframe=bt.TimeFrame.Minutes, compression=3)

    cerebro.broker.setcommission(mult=5, name='A')

    # Add B second data
    cerebro.adddata(dataA)                     
    # Add B minute data 
    cerebro.resampledata(dataA, timeframe=bt.TimeFrame.Minutes, compression=3)

    cerebro.broker.setcommission(mult=0.5, name='B')
       
    # Add strategy to cerebro
    cerebro.addstrategy(TestStrategy)
   
    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.plot(style='candlestick')