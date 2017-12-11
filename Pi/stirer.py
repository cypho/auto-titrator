#!/usr/bin/env python
import RPi.GPIO 
import time
import pigpio
import os
from config import config

class Stirrer(object):
    """Magentetic Stirrer Driver"""
    p = 0
    def __init__(self):
        RPi.GPIO.setwarnings(False)
        RPi.GPIO.setmode(RPi.GPIO.BCM)  
        RPi.GPIO.setup(config.stirrer_enabled_pin, RPi.GPIO.OUT)
        RPi.GPIO.output(config.stirrer_enabled_pin,1)

        RPi.GPIO.setup(config.stirrer_an1_pin, RPi.GPIO.OUT)
        RPi.GPIO.setup(config.stirrer_an2_pin, RPi.GPIO.OUT)
        
        self.clockwise()
        
        self.pi=pigpio.pi()
        if not self.pi.connected:
            os.system("sudo pigpiod")
            time.sleep(30)
            self.pi=pigpio.pi()

    def setPercent(self,p, f=2.0):
        p = float(p)
        f = float(f)
        
        for i in range(100):
            j = self.p + i*(p-self.p)
            if j < 0:
                j = 0.0
            self.pi.hardware_PWM(config.stirrer_pwm_pin, 10000, j*10000.0)
            time.sleep(f/2.0/100.0)
        self.p = p
        self.pi.hardware_PWM(config.stirrer_pwm_pin, 10000, 100.0*p*10000.0)
    
    def clockwise(self):
        RPi.GPIO.output(config.stirrer_an1_pin,1)
        RPi.GPIO.output(config.stirrer_an2_pin,0)
    def counterclockwise(self):
        RPi.GPIO.output(config.stirrer_an1_pin,0)
        RPi.GPIO.output(config.stirrer_an2_pin,1)
            
    def upAndDown(self,p,f,t):
        self.clockwise()
        p = float(p)
        t = float(t)
        f = float(f)
        j=0
        while f*j<t:
            for i in range(100):
                self.pi.hardware_PWM(config.stirrer_pwm_pin, 10000, i*p*10000.0)
                time.sleep(f/2/100)

            for i in range(100):
                self.pi.hardware_PWM(config.stirrer_pwm_pin, 10000, (100-i)*p*10000.0)
                time.sleep(f/2/100)
            j=j+1
            if j%2==0:
                self.clockwise()
            else:
                self.counterclockwise()
        self.p = 0
                

    