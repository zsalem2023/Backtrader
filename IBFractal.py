from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt

import datetime as datetime
import logging
import FractalIndicators as FI
from backtrader.indicators import EMA

# Disable debug logging for matplotlib
logging.getLogger('matplotlib').setLevel(logging.ERROR)


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('fractal_period', 5),
        ('profit_percent', 10), # input hundreths of one percent 
        ('loss_percent', 10),   # input hundreths of one percent 
        ('tick_size', 0.25),
        ('dolog', False)
    )

    def log(self, txt, dt=None, dolog=None, indent=False):
        dolog = dolog or self.p.dolog
        if dolog:
            dt = dt or self.datas[0].datetime.date(0)
            if indent: txt = "            " + txt
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep references
        self.seconds = self.datas[0]
        self.minutes = self.datas[1]

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.pending_entry_order = False

        # Add a Fractal indicator
        self.fractal = FI.Fractal(
            self.minutes, period=self.p.fractal_period, dolog=self.p.dolog
        )

        # Add a Fractal Momentum indicator
        self.momentum = FI.FractalMomentum(
            self.minutes, period=self.p.fractal_period*2
        )

        # Add a Polarized Fractal Efficiency indicator
        self.pfe = EMA(
            self.momentum.l.momentum, period=self.p.fractal_period
        )
        self.pfe.plotinfo.subplot = True
        self.pfe.plotinfo.plotname = 'PFE'
        
        

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
        self.log('Minutes Close, %.2f' % self.minutes.close[0], dt=self.minutes.datetime.datetime(0))
        self.log('Seconds Close, %.2f' % self.seconds.close[0], dt=self.seconds.datetime.datetime(0), indent=True)

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.pending_entry_order:
            return

        # Check if we are in the market
        if not self.position:

            # Grab high and low of current second
            seconds_high = self.seconds.high[0]
            seconds_low = self.seconds.low[0]

            # Buy if broke above up last up fractal
            if seconds_high > self.fractal.last_fractals['up'] and self.fractal.last_fractals['up'] != 0:

                # Set main entry price as trigger price plus $0.50
                entry_price = seconds_high + 0.50
                profit_taker = entry_price * (1 + self.p.profit_percent / 10000)
                stop_loss = entry_price * (1 - self.p.loss_percent / 10000)

                self.log('BUY BRACKET | MAIN: {}  PROFIT TAKER: {}  STOP LOSS: {}'.format(entry_price, profit_taker, stop_loss))

                self.fractal.last_fractals['up'] = 0

                # Keep track of the created order to avoid a 2nd order
                stopinfo = {'price': stop_loss,
                            'pricelimit': stop_loss - self.p.tick_size,
                            'exectype': bt.Order.StopLimit}
                self.order = self.buy_bracket(price = entry_price, limitprice=profit_taker, stopargs=stopinfo)
                self.pending_entry_order = True

            # Sell if broke below last down fractal
            elif seconds_low < self.fractal.last_fractals['down'] and self.fractal.last_fractals['down'] != 0:
                
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
    store = bt.stores.IBStore(host='127.0.0.1', port=7496, _debug=False)
    data = store.getdata(dataname='ES-202006-GLOBEX',
                         #sectype='',
                         #exch='',
                         #curr='',
                         #expiry='',
                         #strike='',
                         #right='',
                         historical=True,
                         timeframe=bt.TimeFrame.Seconds,
                         compression=5,
                         fromdate=datetime.datetime(2020, 3, 31, 9),
                         todate=datetime.datetime(2020, 3, 31, 16)
    )
    # Add second data
    cerebro.adddata(data)                     
    # Add minute data 
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=3)
       
    # Add strategy to cerebro
    cerebro.addstrategy(TestStrategy)
   
    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.plot(style='candlestick')