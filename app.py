import csv
import math
import os
import sys
import uuid
from datetime import datetime, timezone

import boto3
import psycopg2
import sunrise

import rds_config

STATION_LAT = 42.021533
STATION_LON = -71.2179947


# Supporting functions

def calc_dewpoint(temp, rh):
    """Calculate dew point in Celcius from temperature in Celcius and relative
        humidity.

    :param temp: Temperature in Celcius
    :param rh: Relative humidity in % (e.g. 48.0)
    :return: Dew point in Celcius as Float. On error (e.g. rh <= 0) 
        return -100.000
    """

    temp = float(temp)
    rh = float(rh)
    CONST_A = 17.625
    CONST_B = 243.04
    rh = rh / 100.0
    try:
        atbt = (CONST_A * temp) / (CONST_B + temp)
        dewp = CONST_B * (math.log(rh) + atbt)
        dewp = dewp / (CONST_A - math.log(rh) - atbt)
        return round(dewp, 3)
    except ValueError:
        #print("Error with values temp: {} rh: {}".format(temp, rh))
        return -100.000
    
def to_f(temp):
    """Convert a Celcius temperature to Fahrenheit

    :param temp:Temperature in Celcius
    :return: Fahrenheit temperature as Float rounded to 3 decimal places
    """
    temp = float(temp)
    return round((temp * (9.0 / 5.0)) + 32.0, 3)
     
s3_client = boto3.client('s3')

def insert_records(readings):
    """Insert processed readings into database

    :param readings: List of tuples with data to insert
    """
    
    # Create RDS connection
    conn = psycopg2.connect(host=rds_config.db_endpoint,
                            database=rds_config.db_database,
                            user=rds_config.db_username,
                            password=rds_config.db_password)

    sql = """
        INSERT INTO public.readings(datetime, year, month, day, hour, minute,
            second, sunlight_mins, temp, rh, dewp, id, sensor_id) 
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        """
    cursor = conn.cursor()
    
    for reading in readings:
        cursor.execute(sql, reading)
    
    conn.commit()
    cursor.close()
    print('readings inserted')
     
def process_readings_file(file_path):
    """Process sensor data to calculate minutes of sunlight,
       convert temperature to Fahrenheit, and calculate dew point.

    :param file_path: Local path to file to parse
    """

    readings = []
    with open(file_path, mode='r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            # Try to parse datetime of first field in row. If can't parse,
            # the temperature reading script had an error so skip this row.
            try:
                if row[0][1] == '-':
                	dt = datetime.strptime(row[0].split('-', 1)[1], '%Y-%m-%d %H:%M:%S')
                else:
                	dt = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
            # Define that the timezone of the datetime is UTC
            dt = dt.replace(tzinfo=timezone.utc)
            # Get sunrise and sunset time for this location on the reading date
            #s = sunrise.sun(lat=STATION_LAT,long=STATION_LON)
            #s_rise = datetime.combine(dt.date(), 
            #                          s.sunrise(when=dt)
            #                         ).replace(tzinfo=timezone.utc)
            #s_set = datetime.combine(dt.date(), 
            #                          s.sunset(when=dt)
            #                        ).replace(tzinfo=timezone.utc)
            # Calculate minutes of sunlight
            #sun_mins = 0.0 if dt > s_set else round((dt - s_rise).total_seconds() / 60.0, 2)
            sun_mins = 0
            # Add reading to main list
            reading = (
                str(dt), # datetime
                dt.year,
                dt.month,
                dt.day,
                dt.hour,
                dt.minute,
                dt.second,
                sun_mins,
                to_f(row[2]), # temp in F
                float(row[3]), # RH
                to_f(calc_dewpoint(row[2],row[3])), # dew point in F
                row[4], # uuid
                row[1] # sensor ID
            )
            readings.append(reading)

    insert_records(readings)

     
def handler(event, context):
    """Handle S3 file upload event, parse the file, and insert into RDS
    """

    # Process records
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key'] 
        download_path = '/tmp/{}/{}'.format(uuid.uuid4(), key)

        # Create directory structure if needed
        if not os.path.exists(os.path.dirname(download_path)):
            os.makedirs(os.path.dirname(download_path))

        # Download and process file
        s3_client.download_file(bucket, key, download_path)
        process_readings_file(download_path)
