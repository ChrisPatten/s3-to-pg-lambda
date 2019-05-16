#! /usr/bin/python3

import time
from datetime import datetime
import os
import glob
import uuid

SENSOR_ID = 1
SENSOR_TYPE = 'DS18B20'  # Set to DS18B20 or DHT11
GPIO_PIN = 14  # Set to GPIO pin used by DHT11
DHT11_RETRIES = 10

if SENSOR_TYPE == 'DS18B20':
    # Read from DS18B20

    base_dir = '/sys/bus/w1/devices/'
    device_folder_list = glob.glob(base_dir + '28*')
    if len(device_folder_list) > 0:
        device_file = device_folder_list[0] + '/w1_slave'
        sensor_found = True
    else:
        sensor_found = False

    
    def read_temp_raw():
        f = open(device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    
    def read_temp():
        lines = read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c

    if sensor_found:
        temp = read_temp()
    else:
        temp = -100.0

    humidity = 0.1

elif SENSOR_TYPE == 'DHT11':
    import dht11
    import RPi.GPIO as GPIO

    
    def read_dht11():

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)  # Use BCM GPIO numbers
        instance = dht11.DHT11(pin = GPIO_PIN)

        humidity_value = 0

        # Do this in a loop since the reading only works ~1/8 of the time
        retries = 0
        while humidity_value == 0 and retries <= DHT11_RETRIES:
            result = instance.read()
            humidity_value = result.humidity_value
            temperature_value = result.temperature
            retries += 1
            if humidity_value == 0:
                time.sleep(1)
        
        return humidity_value, temperature_value

    humidity, temp = read_dht11()

curr_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

print("{0},{1},{2:3.3f},{3},{4}".format(curr_time, SENSOR_ID, temp, humidity, uuid.uuid4()))
