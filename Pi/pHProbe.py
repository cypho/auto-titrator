#!/usr/bin/env python
import smbus
import time
import traceback
import sys
import numpy as np
from config import config

class pHProbe(object):
    """pH Driver"""
        
    def __init__(self, sampleTime = 10, samples=1000):
        
        self.i2cAddr = config.pH_addr
        self.i2c = smbus.SMBus(1)
        
        if sampleTime is not None:
            self.sampleTime = float(sampleTime)
        if samples is not None:
            self.samples = float(samples)
        
    def value(self, sampleTime = None, samples=None, stable=0, unit='pH', verbose=False):
        
        if sampleTime is not None:
            self.sampleTime = float(sampleTime)
            self.samples = int(float(sampleTime)*100.0)
        if samples is not None:
            self.samples = int(samples)
        
        if stable is None:
            return self._value(unit)
        
        time.sleep(self.sampleTime)
        
        v1 = self._value(unit)
        if verbose:
            print v1
        v2 = self._value(unit)
        if verbose:
            print v2
        v3 = self._value(unit)
        if verbose:
            print v3
        if v1 > v3 and stable < 1:
            while min([v1,v2,v3]) != v1:
                v1 = v2
                v2 = v3
                v3 = self._value(unit)
                if verbose:
                    print v3, 'not stable'

        if v1 < v3 and stable > -1:
            while max([v1,v2,v3]) != v1:
                v1 = v2
                v2 = v3
                v3 = self._value(unit)
                if verbose:
                    print v3, 'not stable'
        return v1

    def _value(self, unit='pH'):
        
        readings = []
        errors = []
        for x in range(0, int(self.samples)):
            try:
                reading = self.i2c.read_i2c_block_data( self.i2cAddr, 0x00, 2)
            except Exception:
                errors.append( traceback.format_exc(sys.exc_info()) )
            else:
                readings.append( ( reading[0] << 8) + reading[1] )

            if self.samples > 1:
                time.sleep(self.sampleTime/self.samples) 

        if len(errors) > self.samples * 0.5:
            raise ValueError(errors)
        
        result = {}
        result['raw'] = self.process(readings)
        
        if ( result['raw'] < config._7_cal_raw or config._4_cal_raw is None ) and config._10_cal_raw is not None:
            result['pH'] = ( config._7_cal_pH + ( ( result['raw'] - config._7_cal_raw) / ( (config._7_cal_raw - config._10_cal_raw) / (config._7_cal_pH - config._10_cal_pH) ) ) )
            
        if ( result['raw'] >= config._7_cal_raw or config._10_cal_raw is None ) and config._4_cal_raw is not None:
            result['pH'] = ( config._7_cal_pH + ( ( result['raw'] - config._7_cal_raw) / ( (config._7_cal_raw - config._4_cal_raw) / (config._7_cal_pH - config._4_cal_pH) ) ) )
            
        
        return result[unit]
        
    def process(self,x):
        outlierConstant = 1.5
        a = np.array(x)
        upper_quartile = np.percentile(a, 75)
        lower_quartile = np.percentile(a, 25)
        IQR = (upper_quartile - lower_quartile) * outlierConstant
        quartileSet = (lower_quartile - IQR, upper_quartile + IQR)
        resultList = []
        for y in a.tolist():
            if y >= quartileSet[0] and y <= quartileSet[1]:
                resultList.append(y)
        return np.average(resultList)

