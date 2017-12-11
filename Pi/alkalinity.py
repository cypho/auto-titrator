#!/usr/bin/env python
import sys
import time
import datetime
import traceback
import MySQLdb
import base64
import json
import numpy as np
from copy import deepcopy
from config import config
import calendar
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from dosingPump import DosingPump
from pHProbe import pHProbe
from stirer import Stirrer

class alkTitration(object):
    endPoint = 4.5
    preDose = 0.0
    data = { 'alkalinity': [],'pH': [], 'sampletime':[0,0], 'samplesize':10.0}
    def __init__(self):
        
        self.storageVolume = 12.0
        
        self.primeSample = 6.0
        self.primeReagent = 0.1
        
        self.rinse1 = 5.0
        self.rinse2 = 2
        
        self.drain   = DosingPump(config.drain_addr, config.drain_pump, config.drain_calib)
        self.rinse   = DosingPump(config.rinse_addr, config.rinse_pump, config.rinse_calib)
        self.sample  = DosingPump(config.sample_addr,config.sample_pump,config.sample_calib)
        self.reagent = DosingPump(config.hcl_addr,   config.hcl_pump,   config.hcl_calib)
        
        self.pH = pHProbe()
        self.stir = Stirrer()
        
    def start(self, endPoint=None, sampleSize=None, preDose = None):
        
        if endPoint is not None:
            self.endPoint = endPoint
        if sampleSize is not None:
            self.data['samplesize'] = sampleSize
        if preDose is not None:
            self.preDose = preDose
        
        self.drain.setConfig(DosingPump.forward,DosingPump.microsteps_16,rpm=255)
        self.rinse.setConfig(DosingPump.forward,DosingPump.microsteps_16,rpm=255)
        self.sample.setConfig(DosingPump.forward,DosingPump.microsteps_16,rpm=255)
        self.reagent.setConfig(DosingPump.forward,DosingPump.microsteps_16,rpm=255)
        
        startTime = calendar.timegm(time.gmtime())

        self.startPrime()
        self.startRinse()
        self.prepareSample()
        self.startTitration()
        self.cleanup()
        self.analyse()
        print 'Total Test time: {} minutes.'.format((calendar.timegm(time.gmtime())-startTime)/60)
        
    def startPrime(self):
        
        print 'Starting prime and drain.'
        primeStart = calendar.timegm(time.gmtime())

        self.stir.setPercent(.15)

        self.reagent.start(ml=self.primeReagent, wait=False)
        self.sample.start(ml=self.primeSample,wait=False)
        self.drain.start(ml=self.storageVolume+self.primeReagent+2,wait=True)
        print '    Done'
        print '    It took {} minutes to prime and drain'.format((calendar.timegm(time.gmtime())-primeStart)/60)

    def startRinse(self):

        print 'Starting rinse.'
        startRinse = calendar.timegm(time.gmtime())

        self.rinse.start(ml=self.rinse1,wait=True)
        self.stir.upAndDown(.7,3,9)
        self.drain.start(ml=self.rinse1+0.25,wait=True)
        
        self.rinse.start(ml=self.rinse2,wait=True)
        self.drain.start(ml=self.rinse2+1,wait=True)
        
        print '    Done'
        print '    It took {} minutes to rinse'.format((calendar.timegm(time.gmtime())-startRinse)/60)
        
    def prepareSample(self):
        
        print 'Preparing sample.'
        startprep = calendar.timegm(time.gmtime())
        
        self.stir.setPercent(.15)
        
        r = self.preDose*self.data['samplesize']/(config.hcl_strength/0.001)
        print '    Adding {} ml sample and {} ml HCl'.format( self.data['samplesize'], r)
        
        self.reagent.setRPM(self.reagent.rpmNeeded(t=self.sample.timeFor(ml=self.data['samplesize']), ml=r))
        self.reagent.start(ml=r,wait=False)
        
        self.data['sampletime'][0] = calendar.timegm(time.gmtime())
        self.data['sampletime'][1] = datetime.datetime.now()
        self.sample.start(ml=self.data['samplesize'],wait=True)
        self.reagent.setRPM(255)
        self.reagent.wait()
        
        self.drain.setDIR(DosingPump.reverse)
        self.drain.start(ml=0.1,wait=True)
        self.drain.setDIR(DosingPump.forward)
        
        self.titrantVolume = r
        
        print '    Done'
        print '    It took {} minutes to prepare sample'.format((calendar.timegm(time.gmtime())-startprep)/60)
        
        
    def startTitration(self):
        
        print 'Starting Titration.'
        startTitrationTime = calendar.timegm(time.gmtime())
        
        self.stir.setPercent(.15)
        stepsize = int(self.data['samplesize']*0.06/config.hcl_strength)*16
        d1 = self.titrate(to=self.endPoint + 0.75, steps=stepsize*3, pHsampleTime=5.0)
        time.sleep(30)
        d2 = self.titrate(to=self.endPoint + 0.3, steps=stepsize*2, pHsampleTime=7.5)
        d3 = self.titrate(to=self.endPoint - 0.2, steps=stepsize*1, pHsampleTime=6.0)
        d4 = self.titrate(to=self.endPoint - 0.65, steps=stepsize*2, pHsampleTime=6.0)
        
        print '    Done'
        print '    It took {} minutes to titrate.'.format((calendar.timegm(time.gmtime())-startTitrationTime)/60)
        
        self.data['pH'] = d2['pH']
        self.data['pH'].extend(d3['pH'])
        self.data['pH'].extend(d4['pH'])
        self.data['alkalinity'] = d2['alkalinity']
        self.data['alkalinity'].extend(d3['alkalinity'])
        self.data['alkalinity'].extend(d4['alkalinity'])
        
    def titrate(self, to, steps, pHsampleTime):
        print '    Titrating to pH of {}'.format(to)
        print '    meq/l         pH'
                   
        data = {}
        data['alkalinity'] = []
        data['pH'] = []
        
        r = self.titrantVolume
        p = self.pH.value(sampleTime=pHsampleTime, stable=True)
        
        while p > to:
            self.reagent.start(steps=steps,wait=True)
            r = r + self.reagent.stepsToML(steps)
            p = self.pH.value(sampleTime=pHsampleTime, stable=True)
            data['alkalinity'].append(r/self.data['samplesize'] * config.hcl_strength/0.001)
            data['pH'].append(p)
            print '    {} {}'.format(r/self.data['samplesize'] * config.hcl_strength/0.001, p)
            
        self.titrantVolume = r
        return data
            
    def analyse(self):
        
        try:
            self.x_all = np.array(self.data['pH'])
            self.y_all = np.array(self.data['alkalinity'])        
            self.fit_all = np.polyfit(self.x_all,self.y_all, 3)
            self.alk_all = np.poly1d(self.fit_all)

            self.endPoint =  (self.fit_all[1]*-2)/(self.fit_all[0]*6)
            self.alkalinity =  self.alk_all(self.endPoint)
        

            print '    Inflection point'
            print '    y = {}pH^3 + {}pH^2 + {}pH + {}'.format(self.alk_all[0],self.alk_all[1],self.alk_all[2],self.alk_all[3])
            print '    pH = {}'.format(self.endPoint)
            print ''
            print 'The alkalinity is {} meq/L'.format(self.alkalinity), 
            print '                  {} dKH'.format(self.alkalinity*2.8)
            print '                  {} ppm'.format(self.alkalinity*50.0)
        
        except Exception:
            print  traceback.format_exc(sys.exc_info())
             
    def plot(self):
        try:
            plt.subplot(111)
            fig = plt.figure()
            fig.suptitle('Alkalinity', fontsize=20 )
            plt.plot(self.x_all, self.alk_all(self.x_all),'--k')
            plt.plot(self.x_all,self.y_all, 'yo')
            plt.plot(self.endPoint,self.alkalinity,'b*',markersize=12)
            plt.xlim(self.data['pH'][0], self.data['pH'][len(self.data['pH'])-1])
            plt.ylim(self.data['alkalinity'][0], self.data['alkalinity'][len(self.data['alkalinity'])-1])
            plt.annotate('Inflection Point at pH '+'{0:.2f}'.format(self.endPoint) ,
                         xy=(self.endPoint, self.alkalinity), xycoords='data',
                         xytext=(-120, +30), textcoords='offset points', fontsize=12,
                         arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=.2'))
            plt.xlabel('pH', fontsize=12, color='black' )
            plt.ylabel('Titrant Volume (meq/L)', fontsize=12, color='black')
            plt.title('{0:.3f} meq/l\n{1:.3f} dKH'.format(self.alkalinity, self.alkalinity*2.8), loc='left')
            plt.title(self.data['sampletime'][1].strftime('%m-%d-%Y\n%I:%M %p'), loc='right')
            plt.savefig(config.save_path+'alk.png',transparent=True)
        
        except Exception:
            print  traceback.format_exc(sys.exc_info())
            
    def log(self):
        try:
            with open(config.save_path+'alk.png') as imgdata:  
                img = base64.b64encode(imgdata.read())
                
            d = deepcopy(self.data)
            d['sampletime'] = self.data['sampletime'][0]
            
            db = MySQLdb.connect(host=config.db_host,user=config.db_user,passwd=config.db_pass,db=config.db_name)
            cur = db.cursor()
            cur.execute('INSERT INTO alkalinity(sampletime,samplesize,inflection,alkalinity,data,polyfit,image) VALUES (FROM_UNIXTIME(%s), %s, %s, %s, %s, %s, %s)', ( 
                d['sampletime'],
                d['samplesize'],
                self.endPoint,
                self.alkalinity, 
                json.dumps(d),
                json.dumps(self.fit_all.tolist()),
                img))
            db.commit()
            cur.close()
            db.close()
            
        except Exception:
            print  traceback.format_exc(sys.exc_info())
        
    def cleanup(self):
        self.stir.setPercent(0.0)
        self.drain.start(ml=self.titrantVolume+self.data['samplesize']-self.storageVolume,wait=False)
        
        self.sample.setDIR(DosingPump.reverse)
        self.sample.start(ml=self.primeSample,wait=True)
        self.sample.setDIR(DosingPump.forward)