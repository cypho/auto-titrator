#!/usr/bin/env python
import math

class config(object):
    
# mySQL database info/credentials
    db_host = 'localhost'
    db_name = 'database'
    db_user = 'username'
    db_pass = 'password'

# If script crashes, before the test ends, the lock file may
# not be deleted. How long is long enough to assume that the
# lock file is a remnant of a failed test and is not a sign 
# that a test is still running? In seconds.
    lock_timeout = 2*60*60-5

# location of log file used when -l or --output_to_log_file 
# option is used
    save_path = '/home/pi/web/'

# A poorly calibrated probe will have no impact on test
# accuracy or precision. In theory the test can be run 
# using raw pH probe data without any calibration values.
# However I have only tested using a calibrated probe.  
# If your calibration way off you may need to tweak other 
# settings.  Probably easier to just calibrate the probe.
# As long as you are getting an inflection point between
# pH 4 and pH 5 the calibration is fine. 

    _4_cal_raw  = 2183.5
    _4_cal_pH   = 4.00
    _7_cal_raw   = 2039.0
    _7_cal_pH    = 7.03
    _10_cal_raw  = 1900.0
    _10_cal_pH   = 10.06
    

# i2c address of pH probe
    pH_addr=0x48

# i2c address, pump location, and calibration for each pump.
# Calibration on rinse and drain don't matter much.  But 
# a good calibration very especially important on the sample 
# and HCl pumps. It will not impact on precision or repeatability
# all that much, but it will have a big impact on accuracy.
# So if the pumps are poorly calibrated you can still achieve
# stable alkalinity. But your alk may be stable at a value different
# than you expected. Calibration units are steps per ml.  

    #Suggested calibration routine:
        # Place the pump input in RO water. Prime the pump. Place the output 
        # in a cup. Then tell the pump to move forward a fixed number of steps.
        # The more steps, the better. When that finishes, weigh the water in gm.
        # Measure the temperature of the water and look up density of water at 
        # that temperature. Or just call the density 1.0. Then:

        # calibration = steps / gm * density (NOTE - value must be an integer)

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
    
# Which pins on the rasperry pi are the motor  driver
# for the stirrer connected to. 
    stirrer_enabled_pin = 17
    stirrer_an1_pin = 27
    stirrer_an2_pin = 22
    stirrer_pwm_pin = 18
    

# Speed of stir bar. Should be fast enough to effectively
# mix the sample.  But if too fast the magnet may not be 
# strong enough to keep a hold of the stir bar. Also faster
# speeds may be noisy. Valid values are 0.0 (off) to 1.0 (max)
    stir_speed = 0.2

# This will depend on how long the sample collection 
# tube is. Units are ml
    primeSample = 6.0
# Pump a small amount of reagent during the prime & drain 
# cycle to make sure that there is no air in the reagent 
# pipet tip. Units are ml
    primeReagent = 0.01

# How much RO water do you want to use to rinse.  More 
# rinsing is never a bad thing, but it can be time 
# consuming. Ideal values will depend on the size and 
# shape of the reaction vial. Units are ml
    rinse1 = 9.0
    rinse2 = 1.0
# How much to drain during an extra_drain cycle. The 
# extra drain cycle runs if the previous test crashed 
# and therefore did not drain. This should be large enough
# to drain the excess liquid from failed test. Units are ml
    extra_drain = 20.0
    
# How much liquid do we leave in the reaction chamber 
# between tests?  Must be enough to keep the tip of 
# the pH probe submerged. Units are ml
    storageVolume = 12.0
    
# Titration Parameters
    
    # Minimum sample size will depend on the size of 
    # vial you are using.  Tip of pH probe must be fully 
    # submerged.  Larger samples will increase precision.
    # Especially with stronger acids you may want to increase.
    # Units are ml
    sampleSize = 14.0
    
    # How long of a time should the pH probe spend taking a
    # reading.  I have not spent much time optimizing this,
    # however I have found that if you increase this too much
    # it slows the titration down too much which is a problem
    # because for some reason the pH will start rising if you
    # go too slow.
    pHsampleTime = 6.0
    
    # I have used 0.01N HCl and 0.1N HCl.  Both worked OK.  
    # With 0.01N acid, bubbles or other pump errors will 
    # have less impact on test precision and accuracy.
    # But using 0.1N acid is cheaper and will last 10x 
    # before you have to refill.    
    hcl_strength = 0.1
    
    # percent of expected alk to predose.  Higher values will
    # speed test, but if set too high you may get a poor 
    # inflection point calculation.  Script output will provide 
    # guidance in optimizing this value. If your alk tends to 
    # fluctuate significantly, you may want to use a lower value
    # than the script's recommendation.
    preDose = 0.90
    
    # Stop titration at this pH.  Higher values will speed test, 
    # but if set too high, you may get a poor inflection point 
    # calculation. Script output will provide guidance in optimizing
    # this value.
    endPoint = 3.7
    
    # The size (in stepper motor steps) of each dose in the titration 
    # is determined by this method. Smaller doses may result in a more 
    # accurate test. But too small and you will start to get inconsistent
    # drops which may reduce the accuracy. Smaller does also slows down 
    # the test. Which can be a problem. For some reason the pH will start
    # rising if you go too slow.
   
    # This function seems to work pretty well for me, but I am sure it can 
    # be improved and you may need to tweak the constants so I am including 
    # function as part of the config.
    
    # increasing part A will result is larger doses over the entire titration
    
        # doubling the sample size will double the size of each dose so you 
        # end up with roughly the same number of doses no matter what the sample
        # size is.
        
        # higher alkalinities will use more acid.  At 2x the alkalinity the
        # doses will be 2x as large so again you should have roughly the same
        # number of doses for at alkalinity
        
        # switching from 0.1N acid to 0.01N acid will increase the size of 
        # each dose 10x so again, you will end up with roughly the same number
        # of doses with either acid. 
        
        # to make all doses smaller, increase the constant at the end of part A
        
    # increasing B will result in larger doses early and late in the 
    # titration when the pH is farther from the expected inflection point
    
        # this allows us to spend more time, and place more weight on the
        # portion of the titration very near the critical inflection point.
        # increasing the base of the exponent will increase magnitude of 
        # this effect.
    
    # The stepper motor powers down between each dose.  When the powers down 
    # it may shift forward/back to the nearest full step so we want to make 
    # sure we always stops on a full step. That is where the 16 in the return
    # comes from.
    
    @staticmethod
    def steps(pH, sampleSize, expectedAlk, hcl_strength, expectedInflectionPoint):
        
        a = math.ceil(sampleSize*expectedAlk / hcl_strength / 65.0) 
        b = (20.0 ** math.fabs( pH-expectedInflectionPoint-0.03))
        
        return int(a*b)*16
    
    
#Result Validation

    # How many times to try before giving up. Make sure that lock
    # timeout is long enough to account for max tries.
    tries = 3
    
    # Results higher/lower than these values are considered invalid.
    # units are meq/l
    max_alk = 5.0
    min_alk = 2.0
    # If the measured alk has changed more than this, we will
    # retest to confirm. Units are meq/l
    max_alk_change = 0.05
    
    # Inflection point should be somewhere around 4.5. Values 
    # higher or lower than these values will be considered 
    # invalid. If your pH probe calibration is way off you may 
    # need to change these limits. Units are pH
    max_inflection = 5.0
    min_inflection = 4.0
    # If the inflection point has changed more than this, we 
    # will retest to confirm. Units are pH
    max_inflection_change = 0.1
    
    # Toss out any results where error is greater than this. 
    # Error is the average difference between measured values
    # and the best fit curve used to calculate inflection point
    # and alkalinity.  Higher than normal error is a sign that
    # the result may be inaccurate. The error could be caused by
    # a number of things, but generally increasing the sample
    # size will reduce the error. So we can increase the sample
    # size for the next test.
    max_err = 0.021
    max_err_multiplyer = 1.25
    
    
    
# If your alkalinity is lower than target. We will calculate the
# amount of chemical needed to raise alkalinity to target. 
    
# Units accepted for target alk are meq/l, dkh, or ppm
# Units accepted for volume are liters, or gallons
# Supported chemicals are SodiumCarbonate,  SodiumBicarbonate or CalciumHydroxide.
# Strength is mg of dry chemical per ml of solution. Use 0 for strength if using 
# dry powered chemical not in a liquid solution.
    
 # target_alk examples
    # target_alk = {"meq/l": 3.0}
    # target_alk = {"dkh": 8.4}
    # target_alk = {"ppm": 150.0}
    
 # dose_with examples
    # Liquid Sodium Bicarbonate solution
    # dose_with = {"chemical": "SodiumBicarbonate", "strength": 78.5 }
    # Dry Sodium Carbonate
    # dose_with = {"chemical": "SodiumCarbonate", "strength": 0.0 }
    # Saturdated Kalkwasser
    # dose_with = {"chemical": "CalciumHydroxide", "strength": 1.479 }
    
    target_alk = {"meq/l": 3.0}
    total_aquarium_volume = {"gallons": 75.0}
    dose_with = {"chemical": "SodiumBicarbonate", "strength": 0.0 }

    
