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
        
    plotinfo = dict(subplot=False, plotlinelabels=True, plot=True)

    plotlines = dict(
        up_fractal=dict(marker='^', markersize=8.0, color='lightgreen',
                             fillstyle='full', ls=''),
        down_fractal=dict(marker='v', markersize=8.0, color='salmon',
                             fillstyle='full', ls='')
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

    lines = ('momentum',)
    params = dict(period=5,)

    def __init__(self, period=5):
        self.minutes = self.datas[0]
        self.addminperiod(period)
        self.p.period = period
        
    plotinfo = dict(subplot=True, plotlinelabels=False, plot=True)

    plotlines = dict(
        momentum=dict(color='blue', fillstyle='full'),
    )

    def next(self):
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
        num = 0
        for i in range(0, self.p.period//2):
            num += self.minutes[-i-1] - self.minutes[-i]
        for i in range(self.p.period//2, self.p.period-2):
            num += self.minutes[-i] - self.minutes[-i-1] 
        den = self.minutes[-self.p.period//2]
        self.l.momentum[0] = 100 * num / den
