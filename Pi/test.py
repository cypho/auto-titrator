#!/usr/bin/env python
import sys; sys.dont_write_bytecode = True
import error_log
from alkalinity import alkTitration
import MySQLdb
import time
import math
import os
import copy
from config import config

if os.path.exists('test_in_progress'):
    print 'test in progress, exiting'
    exit()
open('test_in_progress', 'a').close()


db = MySQLdb.connect(host=config.db_host,user=config.db_user,passwd=config.db_pass,db=config.db_name)
cur = db.cursor()
cur.execute('SELECT alkalinity, inflection FROM alkalinity ORDER BY sampletime DESC LIMIT 1')
row = cur.fetchone()
cur.close()
db.close()

if row is not None:
    previousAlk = row[0]
    previousInflection = row[1]
else:
    previousAlk = 2.0
    previousInflection = 4.5
    
time.sleep(16)
a = alkTitration()

a.start(endPoint=previousInflection, sampleSize=12.0, preDose = (float(previousAlk) - 0.3))
testedAlk = copy.deepcopy(a.alkalinity)

if math.fabs(testedAlk-previousAlk) > 0.05:
    print 'Trying again, change is more that 0.05'
    data = copy.deepcopy(a.data)
    
    a.start(sampleSize=14.0, preDose = min(previousAlk,a.alkalinity) - 0.3)
    
    if(  math.fabs(a.alkalinity-testedAlk) < 0.02 or math.fabs(testedAlk-previousAlk)) < math.fabs(a.alkalinity-previousAlk):
        print 'Going back to origional test result'
        a.data = copy.deepcopy(data)
        a.analyse()

a.plot()
a.log()
os.remove('test_in_progress')