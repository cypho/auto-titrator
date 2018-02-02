#!/usr/bin/env python
import sys
import time
import datetime
import traceback
import MySQLdb
import base64
import math
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

class ResultsObject(object):
    x = None
    y = None
    fit = None
    alk = None
    ip = None
    plot = None
            
class alkTitration(object):
    expectedInflectionPoint = 4.5
    expectedAlk = 2.5
    results = None
    previousAlk = 0
    data = { 'alkalinity': [],'pH': [], 'sampletime':[0,0]}
    def __init__(self, args):
        
        
        self.config = config()
        
        alk, ip, t = self.getLastTest()
        
        if alk is not None:
            self.previousAlk = self.expectedAlk = float(alk)
        if ip is not None:
            self.expectedInflectionPoint = float(ip)
        
        if args.alk is not None:
            if args.dkh is not None:
                c = 2.8
            elif args.ppm is not None:
                c = 50.0
            else:
                c = 1
            self.previousAlk = self.expectedAlk = float(args.alk) * c
            
        if args.ip is not None:
            self.expectedInflectionPoint = float(args.ip)
            
        self.drain   = DosingPump(self.config.drain_addr, self.config.drain_pump, self.config.drain_calib)
        self.rinse   = DosingPump(self.config.rinse_addr, self.config.rinse_pump, self.config.rinse_calib)
        self.sample  = DosingPump(self.config.sample_addr,self.config.sample_pump,self.config.sample_calib)
        self.reagent = DosingPump(self.config.hcl_addr,   self.config.hcl_pump,   self.config.hcl_calib)
        
        self.drain.setConfig(DosingPump.forward,DosingPump.microsteps_16,rpm=255)
        self.rinse.setConfig(DosingPump.forward,DosingPump.microsteps_16,rpm=255)
        self.sample.setConfig(DosingPump.forward,DosingPump.microsteps_16,rpm=255)
        self.reagent.setConfig(DosingPump.forward,DosingPump.microsteps_16,rpm=255)
        
        self.pH = pHProbe()
        self.stir = Stirrer()
        
        if args.extra_drain:
            self.extraDrain()
        
    def start(self):
        
        
        startTime = calendar.timegm(time.gmtime())
        
        tries = 0
        while tries < self.config.tries and self.results is None:
        
            self.startPrime()
            self.startRinse()
            self.prepareSample()
            self.titrate()
            self.getResults()
            self.analyze()
            self.log()
            self.cleanup()
            tries = tries + 1
            
            
        print 'Total Test time: {:.2f} minutes.'.format((calendar.timegm(time.gmtime())-startTime)/60.0)
        
        
    def startPrime(self):
        
        print 'Starting prime and drain.'
        primeStart = calendar.timegm(time.gmtime())

        self.stir.setPercent(self.config.stir_speed)

        self.reagent.start(ml=self.config.primeReagent, wait=False)
        self.sample.setDIR(DosingPump.forward)
        self.sample.start(ml=self.config.primeSample,wait=False)
        self.drain.start(ml=self.config.storageVolume+2.0,wait=True)
        print '    Done'
        print '    It took {:.2f} minutes to prime and drain'.format((calendar.timegm(time.gmtime())-primeStart)/60)

    def extraDrain(self):
        
        print 'Starting Extra Drain.'
        startDrain = calendar.timegm(time.gmtime())
        
        self.drain.start(ml=self.config.extra_drain,wait=True)
        
        print '    Done'
        print '    It took {:.2f} minutes to drain'.format((calendar.timegm(time.gmtime())-startDrain)/60)
        
    def startRinse(self):

        print 'Starting rinse.'
        startRinse = calendar.timegm(time.gmtime())

        self.rinse.start(ml=self.config.rinse1,wait=True)
        self.stir.upAndDown(0.7,3,9)
        self.drain.start(ml=self.config.rinse1+0.25,wait=True)
        
        self.rinse.start(ml=self.config.rinse2,wait=True)
        self.drain.start(ml=self.config.rinse2+1.0,wait=True)
            
        
        print '    Done'
        print '    It took {:.2f} minutes to rinse'.format((calendar.timegm(time.gmtime())-startRinse)/60)
        
    
    def prepareSample(self):
        
        print 'Preparing sample.'
        startprep = calendar.timegm(time.gmtime())
        
        self.stir.setPercent(self.config.stir_speed)
        
        r = (float(self.expectedAlk) * self.config.preDose)*self.config.sampleSize/(self.config.hcl_strength/0.001)
        print '    Adding {:.2f} ml sample and {:.4f} ml HCl'.format( self.config.sampleSize, r)
        
        self.reagent.setRPM(self.reagent.rpmNeeded(t=self.sample.timeFor(ml=self.config.sampleSize), ml=r))
        self.reagent.start(ml=r,wait=False)
        
        self.data['sampletime'][0] = calendar.timegm(time.gmtime())
        self.data['sampletime'][1] = datetime.datetime.now()
        
        self.sample.start(ml=self.config.sampleSize,wait=True)
        self.sample.setDIR(DosingPump.reverse)
        self.sample.start(ml=self.config.primeSample,wait=False)
        
        self.reagent.setRPM(175)
        self.reagent.wait()
        
        self.drain.setDIR(DosingPump.reverse)
        self.drain.start(ml=0.1,wait=True)
        self.drain.setDIR(DosingPump.forward)
        
        self.titrantVolume = r
        
        self.stir.upAndDown(0.8,3,3*5)
        
        print '    Done'
        print '    It took {:.2f} minutes to prepare sample'.format((calendar.timegm(time.gmtime())-startprep)/60)
        
        
    def titrate(self):
        
        print 'Starting Titration.'
        startTitrationTime = calendar.timegm(time.gmtime())
        
        self.stir.setPercent(self.config.stir_speed)
        time.sleep(30)
        
        
        print '  Titrating to pH of {:.2f}'.format(self.config.endPoint)
        print '    meq/l         pH'
                   
        
        r = self.titrantVolume
        p = self.pH.value(sampleTime=self.config.pHsampleTime, stable=-1)
        
        data = {}
        data['alkalinity'] = [r/self.config.sampleSize * self.config.hcl_strength/0.001]
        data['pH'] = [p]
        print '    {:.4f} {}'.format(r/self.config.sampleSize * self.config.hcl_strength/0.001, p)
        
        while p > self.config.endPoint:
            steps = config.steps(p, self.config.sampleSize, self.expectedAlk, self.config.hcl_strength, self.expectedInflectionPoint)
#            steps  = int(math.ceil(self.config.sampleSize*(self.expectedAlk/65.0)/self.config.hcl_strength) * (20 ** math.fabs(p-self.expectedInflectionPoint-0.03)))*16
            self.reagent.start(steps=steps,wait=True)
            r = r + self.reagent.stepsToML(steps)
            p = self.pH.value(sampleTime=self.config.pHsampleTime, stable=-1)
            
            data['alkalinity'].append(r/self.config.sampleSize * self.config.hcl_strength/0.001)
            data['pH'].append(p)
            
            print '    {:.4f} {}'.format(r/self.config.sampleSize * self.config.hcl_strength/0.001, p)
            
        self.titrantVolume = r
        
        
        print '    Done'
        print '    It took {:.2f} minutes to titrate.'.format((calendar.timegm(time.gmtime())-startTitrationTime)/60)
        
        self.data['pH'] = data['pH']
        self.data['alkalinity'] = data['alkalinity']
        
        
            
    def getResults(self):
        
        try:
            x = np.array(self.data['pH'])
            y = np.array(self.data['alkalinity']) 
            fit = np.poly1d(np.polyfit(x,y, 3))
            
            ip  = fit.deriv(2).roots[0]
            alk = fit(ip)
            
        except Exception:
            print  traceback.format_exc(sys.exc_info())
            self.results = None
        else:
            
            self.printResults(alk,ip)
            
            self.results = ResultsObject()
            self.results.x = x
            self.results.y = y
            self.results.fit = fit
            self.results.ip  = ip
            self.results.alk = alk
            self.results.plot = self.plot()
            
    @staticmethod
    def printResults(alk, ip):
        print 'The alkalinity is {:.3f} meq/L'.format(alk)
        print '                  {:.3f} dKH'.format(alk*2.8)
        print '                  {:.1f} ppm'.format(alk*50.0)
        print ''
        print '    Inflection point, pH = {:.2f}'.format(ip)
        alkTitration.raise_alk(alk)
    
    def analyze(self):
        
        try:
            fit = self.results.fit
            ip = self.results.ip
            alk = self.results.alk
            
            err = 0.0
            for idx, pH in enumerate(self.data['pH']):
                err = err + ((math.fabs(fit(pH) - self.data['alkalinity'][idx])))/fit(pH)
            err = err/len(self.data['pH']) * 10.0
            print ''
            print '    Average error is = {:.4f}%'.format(err)
            
            deriv = fit.deriv(1)
            ideal_params = deepcopy(deriv)
            ideal_params.coefficients[2] = ideal_params.coefficients[2]-deriv(ip)*3.0
            ideal_preDose = fit(ideal_params.roots[0])/fit(ip)
            ideal_endPoint = ideal_params.roots[1]
            
            print ''
            print '    Ideal predose (3x IP slope) =  {:.3f}'.format(ideal_preDose)
            print '    Ideal endPoint (3x IP slope) = {:.2f}'.format(ideal_endPoint)
            
#             print '    Slope at inflection point =    {}'.format(deriv(ip))
#             print '    Slope at first point =         {}'.format(deriv(self.data['pH'][0]))
#             print '    Slope at last point =          {}'.format(deriv(self.data['pH'][-1]))
            
            print '    Relative Slope of first data point = {:.1f}'.format( deriv(self.data['pH'][0]) /deriv(ip) )
            print '    Relative Slope of last data point  = {:.1f}'.format( deriv(self.data['pH'][-1])/deriv(ip) )
            
            
            if len(self.data['pH']) < 5:
                print "Too few datapoints."
                self.results = None
            
            if alk > self.config.max_alk or alk < self.config.min_alk:
                print "Alk out of range."
                self.results = None
            
            if ip > self.config.max_inflection or ip < self.config.min_inflection:
                print "Inflection point out of range."
                self.results = None

            if self.results is None:
            
                print "Reset parameters to default/safe values."
                print "Set expected Inflection Point to {:.2f}".format(alkTitration.expectedInflectionPoint)
                print "Set expected Alkalinity to {:.3f}".format(alkTitration.expectedAlk)
                self.expectedInflectionPoint = alkTitration.expectedInflectionPoint
                self.expectedAlk = alkTitration.expectedAlk
                self.results = None
                return
            
            if err > self.config.max_err : 
                print "Too much error in data.  Increasing sample size from {:.1f} to {:.1f}.".format(self.config.sampleSize,self.config.sampleSize * self.config.max_err_multiplyer)
                self.config.sampleSize = self.config.sampleSize * self.conf.max_err_multiplyer
                self.results = None
                return
                
            if math.fabs(self.expectedInflectionPoint - ip) > self.config.max_inflection_change:
                print "Inflection point change is greater than {}".format(self.config.max_inflection_change)
                self.results = None
                
            if self.data['pH'][0] < ip:
                print "Inflection point pH is higher than first data point."
                self.results = None
                
            if self.data['pH'][-1] > ip: 
                print "Inflection point pH is lower than last data point."
                self.results = None
                
            if self.results is None:
                print "Updating expected Alkalinity from {:.3f} to {:.3f}".format(self.expectedAlk, alk)
                print "Updating expected Inflection Point from {:.2f} to {:.2f}".format(self.expectedInflectionPoint,ip)
                self.expectedAlk = alk
                self.expectedInflectionPoint = ip
                return
                
            if math.fabs(self.expectedAlk - alk) > self.config.max_alk_change and math.fabs(self.previousAlk - alk) > 0.05:
                    
                print "Alkalinity change is greater than {}".format(self.config.max_alk_change)
                print "Updating expected Alkalinity from {:.3f} to {:.3f}".format(self.expectedAlk, alk)
                print "Updating expected Inflection Point from {:.2f} to {:.2f}".format(self.expectedInflectionPoint,ip)
                self.previousAlk = self.expectedAlk
                self.expectedAlk = alk
                self.expectedInflectionPoint = ip
                self.results = None
            
            
        except Exception:
            print  traceback.format_exc(sys.exc_info())
            #self.results = None
             
    def plot(self):
        
        try:
            
            ip = self.results.ip
            alk = self.results.alk
            data = self.data
            
            plt.subplot(111)
            fig = plt.figure()
            fig.suptitle('Alkalinity', fontsize=20 )
            x=np.linspace(data['pH'][0], data['pH'][len(data['pH'])-1],400)
            plt.plot(x, self.results.fit(x),'--k')
            plt.plot(self.results.x,self.results.y, 'yo')
            plt.plot(ip,alk,'b*',markersize=12)
            
            plt.xlim(data['pH'][0], data['pH'][len(data['pH'])-1])
            plt.ylim(data['alkalinity'][0], data['alkalinity'][len(data['alkalinity'])-1])
            
            plt.annotate('Inflection Point at pH '+'{0:.2f}'.format(ip) ,
                         xy=(ip, alk), xycoords='data',
                         xytext=(-120, +30), textcoords='offset points', fontsize=12,
                         arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=.2'))
            plt.xlabel('pH', fontsize=12, color='black' )
            plt.ylabel('Titrant Volume (meq/L)', fontsize=12, color='black')
            plt.title('{0:.3f} meq/l\n{1:.3f} dKH'.format(alk, alk*2.8), loc='left')
            plt.title(data['sampletime'][1].strftime('%m-%d-%Y\n%I:%M %p'), loc='right')
            
            plt.savefig(self.config.save_path+'alk.png',transparent=True)
            with open(self.config.save_path+'alk.png') as imgdata:  
                img = base64.b64encode(imgdata.read())
            return img
        except Exception:
            print  traceback.format_exc(sys.exc_info())
            return None
    
    @staticmethod
    def getLastTest():
        try:    
            db = MySQLdb.connect(host=config.db_host,user=config.db_user,passwd=config.db_pass,db=config.db_name)
            cur = db.cursor()
            cur.execute('SELECT alkalinity, inflection, sampletime FROM alkalinity ORDER BY sampletime DESC LIMIT 1')
            row = cur.fetchone()
            cur.close()
            db.close()

            if row is not None:
                return ( float(row[0]), float(row[1]), row[2] )
            else:
                raise ValueError("No previous results found.")
                
        except Exception:
            print  traceback.format_exc(sys.exc_info())
            return (None,None,None)
        
    def log(self):
        if self.results is None:
            print "Result not Logged. Discarding results. Will start over unless max tries has been reached."
            return
        try:    
            d = deepcopy(self.data)
            d['sampletime'] = self.data['sampletime'][0]
            
            db = MySQLdb.connect(host=config.db_host,user=config.db_user,passwd=config.db_pass,db=config.db_name)
            cur = db.cursor()
            cur.execute('INSERT INTO alkalinity(sampletime,samplesize,inflection,alkalinity,data,polyfit,image) VALUES (FROM_UNIXTIME(%s), %s, %s, %s, %s, %s, %s)', ( 
                d['sampletime'],
                self.config.sampleSize,
                self.results.ip,
                self.results.alk,
                json.dumps(d),
                json.dumps(self.results.fit.coefficients.tolist()),
                self.results.plot))
            db.commit()
            cur.close()
            db.close()
            
        except Exception:
            print  traceback.format_exc(sys.exc_info())
        
    def cleanup(self):
        self.stir.setPercent(0.0)
        self.drain.start(ml=self.titrantVolume+self.config.sampleSize-self.config.storageVolume,wait=True)
        
    
    @staticmethod
    def raise_alk(alk):
        chemicals = {
            "SodiumCarbonate":   {"weight":105.9888, "proton_receptors": 2.0},
            "SodiumBicarbonate": {"weight":84.007, "proton_receptors": 1.0},
            "CalciumHydroxide":  {"weight":74.093, "proton_receptors": 2.0},
        }
        alkConversion = {"meq/l":1.0,"dkh":2.8,"ppm":50.0}
        volumeConversion = {"liters":1.0,"gallons":3.78541178}
        
        if "liters" in config.total_aquarium_volume:
            volumeUnit = "liters"
        elif "gallons" in config.total_aquarium_volume:
            volumeUnit = "gallons"
        if "meq/l" in config.target_alk:
            alkUnit = "meq/l"
        elif "dkh" in config.target_alk:
            alkUnit = "dkh"
        elif "ppm" in config.target_alk:
            alkUnit = "ppm"
        if config.dose_with["strength"] == 0.0:
            chemicalUnit = "mg"
            strength = 1.0
        else:
            chemicalUnit = "ml"
            strength = float(config.dose_with["strength"])
        
        target_meq = float(config.target_alk[alkUnit]) * alkConversion[alkUnit]
        current_meq = alk
        
        if target_meq > current_meq:
            
            using  = chemicals[config.dose_with["chemical"]]
            liters = float(config.total_aquarium_volume[volumeUnit]) * volumeConversion[volumeUnit]

            ammount_needed = using['weight']/using['proton_receptors']/1000.0*(target_meq - current_meq)*liters*1000.0*strength
            
            print ''
            print "Alkalinity is low"
            print "Add {:.2f} {} of {} to raise alkalinity from {:.3f} {} to {:.3f} {}".format(ammount_needed,chemicalUnit,config.dose_with["chemical"],current_meq*alkConversion[alkUnit],alkUnit, target_meq*alkConversion[alkUnit],alkUnit)