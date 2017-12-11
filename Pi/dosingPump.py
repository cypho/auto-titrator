#!/usr/bin/env python
import sys; sys.dont_write_bytecode = True
import smbus
import time
import json

class DosingPump(object):
    """Dosing Pump Driver"""
    forward = 47
    reverse = 48
    enabled_yes = 45
    enabled_no = 46
    
    microsteps_16 = 16
    microsteps_8 = 8
    microsteps_4 = 4
    microsteps_2 = 2
    microsteps_1 = 1
    
    def __init__(self, addr=0x10, a_or_b='a', calibration=100000):
        
        self.i2cAddr = addr
        self.i2c = smbus.SMBus(1)
        self.calibration = calibration
        
        if a_or_b == 'a':
            self.enabled_register = 1
            self.stepcount_register = 2
            self.dir_register = 6
            self.ms_register = 7
            self.rpm_register = 8
            self.steps_register = 9
            self.loop_register = 10
        else:
            self.enabled_register = 11
            self.stepcount_register = 12
            self.dir_register = 16
            self.ms_register = 17
            self.rpm_register = 18
            self.steps_register = 19
            self.loop_register = 20
        
    def start(self, ml = 0, steps = 0, wait=False):
        if ml > 0:
            steps = self.mlToSteps(ml)
        if steps > 0:
            steps = int(steps)
            self.i2c.write_i2c_block_data(self.i2cAddr, self.enabled_register, [self.enabled_yes,steps & 0xff,(steps >> 8) & 0xff,(steps >> 16) & 0xff,steps >> 24] )
        else: 
            self.i2c.write_byte_data(self.i2cAddr, self.enabled_register, self.enabled_yes)
              
        if wait:
            time.sleep(steps / (3200.0 * self.rpm / 60.0)+.01)
            self.wait(0.2)
            
    def rpmNeeded(self, ml = 0, steps = 0, t=None):
        if ml > 0:
            steps = self.mlToSteps(ml)
        if steps > 0:
            steps = int(steps)
        if t is None:
            return None

        return steps / t * 60.0 / 3200.0 
        
    def timeFor(self, ml = 0, steps = 0, rpm=None):
        if ml > 0:
            steps = self.mlToSteps(ml)
        if steps > 0:
            steps = int(steps)
        if rpm is None:
            rpm = self.rpm
        return steps / (3200.0 * rpm / 60.0)
            
    def wait(self, t=1.0):
        time.sleep(t)
        while self.enabled():
            time.sleep(t)
                
    def stop(self, ml = False, steps = False):
        self.i2c.write_byte_data(self.i2cAddr, self.enabled_register, self.enabled_yes)
        if ml:
            return self.getML()
        if steps:
            return self.getSteps()
        
    def setDIR(self,d):
        self.i2c.write_byte_data(self.i2cAddr, self.dir_register, d)
        self.dir = d
        
    def setMS(self,ms):
        ms = int(round(ms))
        if ms != 1 and ms != 2 and ms !=4  and ms != 8 and ms != 16:
            ms = 16
        self.i2c.write_byte_data(self.i2cAddr, self.ms_register, ms)
        self.ms = ms
        
    def setRPM(self,rpm):
        rpm = int(round(rpm))
        if rpm > 255:
            rpm = 255
            self.i2c.write_byte_data(self.i2cAddr, self.rpm_register, rpm)
            self.rpm=rpm
        
    def setConfig(self, d, ms, rpm):
        
        ms = int(round(ms))
        if ms != 1 and ms != 2 and ms !=4  and ms != 8 and ms != 16:
            ms = 16
        
        rpm = int(round(rpm))
        if rpm > 255:
            rpm = 255
        self.i2c.write_i2c_block_data(self.i2cAddr, self.dir_register, [d,ms,rpm] )
        self.dir = d
        self.ms = ms
        self.rpm = rpm
    
    def setSteps(self,steps):
        self.i2c.write_i2c_block_data(self.i2cAddr, self.stepcount_register, [steps & 0xff,(steps >> 8) & 0xff,(steps >> 16) & 0xff,steps >> 24] )
        
    def setML(self,ml):
        self.setSteps(self.mlToSteps(ml))
        
    def enabled(self):
        
        self.i2c.write_byte(self.i2cAddr, self.enabled_register )
        if self.i2c.read_byte(self.i2cAddr) == self.enabled_no:
            return False
        return True

    def getSteps(self):
        self.i2c.write_byte(self.i2cAddr, self.stepcount_register )
        r0 = self.i2c.read_byte(self.i2cAddr)
        r1 = self.i2c.read_byte(self.i2cAddr)
        r2 = self.i2c.read_byte(self.i2cAddr)
        r3 = self.i2c.read_byte(self.i2cAddr)
        return (r3 << 24) | (r2 << 16) | (r1 << 8) | (r0 );
    
    def mlToSteps(self,ml):
        return int(round(ml*self.calibration))
    
    def stepsToML(self,steps):
        return float(steps)/float(self.calibration)
    
    def getML(self):
        steps = self.getSteps()
        return self.stepsToML(steps)
        
