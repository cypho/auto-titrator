#!/usr/bin/env python

class config(object):
    
    db_host = 'localhost'
    db_name = 'username'
    db_user = 'database'
    db_pass = 'password'
    
    save_path = '/home/pi/'
    
    _4_cal_raw  = 2183.5
    _4_cal_pH   = 4.00
    _7_cal_raw   = 2039.0
    _7_cal_pH    = 7.03
    _10_cal_raw  = 1900.0
    _10_cal_pH   = 10.06
    
    pH_addr=0x4f
    
    drain_addr = 0x13
    drain_pump = 'b'
    drain_calib = 81145
    
    rinse_addr = 0x13
    rinse_pump = 'a'
    rinse_calib = 65060
    
    sample_addr = 0x12
    sample_pump = 'a'
    sample_calib = 74288
    
    hcl_addr = 0x12
    hcl_pump = 'b'
    hcl_calib = 80441
    
    hcl_strength = 0.01
    
    stirrer_enabled_pin = 17
    stirrer_an1_pin = 27
    stirrer_an2_pin = 22
    stirrer_pwm_pin = 18