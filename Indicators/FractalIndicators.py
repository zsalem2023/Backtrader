from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
from backtrader.indicators import EMA
import math

class Fractal(bt.Indicator):

    lines = ('up_fractal', 'down_fractal',)
    params = dict(period=5, exit_movement=0.1, dolog=False)
    last_fractals = {'up': 0, 'down': 0}

    def __init__(self, period=5, dolog=False):
        self.addminperiod(period)
        self.p.period = period
        self.p.dolog = dolog
        
    plotinfo = dict(subplot=False, plotlinelabels=True, plot=True, plotlinevalues=False, plotlinetags=False)

    plotlines = dict(
        up_fractal=dict(marker='^', markersize=8.0, color='lightgreen',
                             fillstyle='full', ls='', _name='Up Fractal'),
        down_fractal=dict(marker='v', markersize=8.0, color='salmon',
                             fillstyle='full', ls='', _name='Down Fractal')
    )

    def log(self, msg, dolog=False, dt=None):
        if dolog:
            dt = dt or self.datas[0].datetime.datetime(0)
            print('%s, %s' % (dt.isoformat(), msg))

    def next(self):
        last_highs = self.data.high.get(size=self.p.period)
        last_lows = self.data.low.get(size=self.p.period)

        # Set default value, unsure if current price will be fractal
        self.l.up_fractal[0] = 0
        self.l.down_fractal[0] = 0
        mid_index = self.p.period//2

        # An up fractal forms when the last_highs are sorted in ascending order from the first to the middle,
        # and sorted in descending order from the middle to the last

        high_one = last_highs[0:mid_index+1]
        high_sort_one = sorted(high_one)
        high_two = last_highs[mid_index:]
        high_sort_two = sorted(high_two, reverse=True)
        
        if (list(high_sort_one) == list(high_one) and list(high_sort_two) == list(high_two) and \
            all(last_highs[i] != last_highs[i+1] for i in range(self.p.period-1))):
            self.l.up_fractal[-2] = self.last_fractals['up'] = last_highs[mid_index]
            self.log("FORMED: Up fractal @" + str(self.last_fractals['up']), dolog=self.p.dolog, dt=self.data.close.get(ago=2, size=1))

        # A down fractal forms when the last_lows are sorted in descending order from the first to the middle,
        # and sorted in ascending order from the middle to the last

        low_one = last_lows[0:mid_index+1]
        low_sort_one = sorted(low_one, reverse=True)
        low_two = last_lows[mid_index:]
        low_sort_two = sorted(low_two)

        if (list(low_sort_one) == list(low_one) and list(low_sort_two) == list(low_two) and \
            all(last_lows[i] != last_lows[i+1] for i in range(self.p.period-1))):
            self.l.down_fractal[-2] = self.last_fractals['down'] = last_lows[mid_index]
            self.log("FORMED: Down fractal @" + str(self.last_fractals['down']))

class FractalMomentum(bt.Indicator):

    lines = ('up_momentum','down_momentum')
    params = dict(period=5,)

    def __init__(self, period=5):
        self.minutes = self.datas[0]
        self.addminperiod(period*2)
        self.p.period = period
        
    plotinfo = dict(subplot=True, plotlinelabels=False, plot=True, plotlinevalues=False, plotlinetags=False, plotabove=False)

    plotlines = dict(
        up_momentum=dict(color='green', fillstyle='full', _name='Up Momentum', _plotskip=True),
        down_momentum=dict(color='red', fillstyle='full', _name='Down Momentum', _plotskip=True),
    )

    def next(self):
        # original PFE
        # num = math.sqrt((self.minutes[0] - self.minutes[-1*self.p.period])**2 + self.p.period**2)
        # den = 0
        # for j in range(0, self.p.period-1):
        #     den += (self.minutes[-j] - self.minutes[-j-1])**2
        # den += 1
        # den = math.sqrt(den)
        # sign = 1
        # if (self.minutes[0] < self.minutes[-1]):
        #     sign = -1
        # self.l.momentum[0] = sign * 100 * num / den

        # EQ's up and down momentum
        # up
        min_highs = min(self.minutes.high.get(size=self.p.period*2))
        num = math.sqrt((self.minutes.close[0] - min_highs)**2 + (self.p.period*2)**2)
        den = 0
        for j in range(1, self.p.period*2):
            den += (self.minutes.close[0] - self.minutes.high[-j])**2 + 1
        den = math.sqrt(den)
        self.l.up_momentum[0] = 100 * num / den - 25
        # down
        max_lows = max(self.minutes.low.get(size=self.p.period*2))
        num = math.sqrt((self.minutes.close[0] - max_lows)**2 + (self.p.period*2)**2)
        den = 0
        for j in range(1, self.p.period*2):
            den += (self.minutes.close[0] - self.minutes.low[-j])**2 + 1
        den = math.sqrt(den)
        self.l.down_momentum[0] = 100 * num / den - 25


class FractalMomentumCD(bt.Indicator):

    lines = ('con_div',)
    params = dict(period=5,)

    def __init__(self, up, down, period=5):
        self.p.period = period
        self.l.con_div = up - down
        
    plotinfo = dict(subplot=True, plotlinelabels=False, plot=True, plotlinevalues=False, plotlinetags=False, plotyticks=[-100,-50,0,50,100])

    plotlines = dict(
        con_div=dict(color='blue', fillstyle='full', _name='Convergence/Divergence')
    )

class FractalDiff(bt.Indicator):

    lines = ('up_fractal','down_fractal','up_diff','down_diff')
    params = dict(period=5,mult=1)

    def __init__(self, period=5, mult=1):
        self.addminperiod(period)
        self.p.period = period
        self.p.mult = mult
        
    plotinfo = dict(subplot=True, plotlinelabels=True, plot=True, plotlinevalues=False, plotlinetags=False)

    plotlines = dict(
        up_fractal=dict(_plot=False),
        down_fractal=dict(_plot=False),
        up_diff=dict(color='lightgreen', fillstyle='full', ls='', _name='Up Diff'),
        down_diff=dict(color='salmon', fillstyle='full', ls='', _name='Down Diff')
    )

    def next(self):
        last_highs = self.data.high.get(size=self.p.period)
        last_lows = self.data.low.get(size=self.p.period)

        # Set default value, unsure if current price will be fractal
        self.l.up_fractal[0] = 0
        self.l.down_fractal[0] = 0
        self.l.up_diff[0] = 0
        self.l.down_diff[0] = 0
        mid_index = self.p.period//2

        # An up fractal forms when the last_highs are sorted in ascending order from the first to the middle,
        # and sorted in descending order from the middle to the last

        high_one = last_highs[0:mid_index+1]
        high_sort_one = sorted(high_one)
        high_two = last_highs[mid_index:]
        high_sort_two = sorted(high_two, reverse=True)
        
        if (list(high_sort_one) == list(high_one) and list(high_sort_two) == list(high_two) and \
            all(last_highs[i] != last_highs[i+1] for i in range(self.p.period-1))):
            self.l.up_fractal[-2] = self.last_fractals['up'] = last_highs[mid_index]
        else:
            self.l.up_fractal[-2] = self.l.up_fractal[-3]
        
        self.l.up_diff[-2] = self.p.mult*(self.l.up_fractal[-2] - self.l.data.high[-2])

        # A down fractal forms when the last_lows are sorted in descending order from the first to the middle,
        # and sorted in ascending order from the middle to the last

        low_one = last_lows[0:mid_index+1]
        low_sort_one = sorted(low_one, reverse=True)
        low_two = last_lows[mid_index:]
        low_sort_two = sorted(low_two)

        if (list(low_sort_one) == list(low_one) and list(low_sort_two) == list(low_two) and \
            all(last_lows[i] != last_lows[i+1] for i in range(self.p.period-1))):
            self.l.down_fractal[-2] = self.last_fractals['down'] = last_lows[mid_index]
        else:
            self.l.down_fractal[-2] = self.l.down_fractal[-3]

        self.l.down_diff[-2] = self.p.mult*(self.l.down_fractal[-2] - self.l.data.low[-2])