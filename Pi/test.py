#!/usr/bin/env python

# uncomment this next line if you don't want your folder cluttered with .pyc files
import sys; sys.dont_write_bytecode = True

import time
import os
import argparse
from config import config
from alkalinity import alkTitration

parser = argparse.ArgumentParser()
parser.add_argument("--get_previous_test", action="store_true", help="Output most recent test result and exit")
parser.add_argument("-f", "--force", help="Ignore lock file", action="store_true")
parser.add_argument("-e", "--extra_drain", help="Do extra drain", action="store_true")
parser.add_argument("-l", "--output_to_log", help="Redirect output to log", action="store_true")
parser.add_argument("-a", "--alkalinity", type=float, dest="alk", help="Use this to supply expected alkalinity instead of looking at the most recent test result in database. Units assumed to be meq/l unless --dkh or --ppm flags are used.")
parser.add_argument("--dkh", action="store_true", help="expected alkalinity units are dkh")
parser.add_argument("--ppm", action="store_true", help="expected alkalinity units are ppm")

parser.add_argument("-i", "--inflection_point", type=float, dest="ip", help="Use this to supply expected inflection point instead of looking at the most recent test result in database.")
args = parser.parse_args()

# do you want output to go to stdout or to log file
if args.output_to_log:
    import error_log

if args.get_previous_test:
    alk,ip,t = alkTitration.getLastTest()
    print t
    alkTitration.printResults(alk,ip)
    exit()
    
# We don't want to run more than one test at a time so check if script is running
if os.path.exists('test_in_progress') and not args.force:
        # if the lockfile is very old, that probably indicates the script crashed
        # so it should be safe to procede.
        if os.path.getmtime('test_in_progress') <= time.time() - config.lock_timeout:
            print 'lock is old, deleting'            
            os.remove('test_in_progress')
            # Do an extra drain in case the crash left extra liquid in chamber
            args.extra_drain = True
        # lockfile is not old, another test is in progrss, so exit
        else:
            print 'test in progress, exiting'
            exit()
# create lock file
open('test_in_progress', 'a').close()


a = alkTitration(args)
a.start()

# we are done, remove lockfile
os.remove('test_in_progress')