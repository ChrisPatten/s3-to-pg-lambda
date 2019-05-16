#! /usr/bin/python3

import logging
import boto3
from botocore.exceptions import ClientError
import argparse
import os
import glob
from datetime import datetime
import dateutil.parser
import sys
import sensor_config

LAST_UPLOAD_FILENAME = 'last_upload_date.txt'

# Get sensor ID from arguments
parser = argparse.ArgumentParser()
parser.add_argument("-p",
                    "--path",
                    help="Absolute path to folder containing logs")
args = parser.parse_args()
if args.path:
  folder_path = args.path
else:
  raise ValueError("--path must be provided")

def upload_file(file_name, bucket, object_name=None):
    """Upload a file into an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name
        is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client(
        's3',
        aws_access_key_id=sensor_config.access_key_id,
        aws_secret_access_key=sensor_config.secret_access_key
    )
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def get_last_date(path):
    """Get the last uploaded date from a directory of log files. Expects
    to find a file with name from LAST_UPLOAD_FILENAME with an ISO 8601 format
    (YYYY-MM-DDTHH:MM:SS) string as its only contents.

    :param path: Path to directory of log files
    :return: DateTime object of last file uploaded or epoch if no date found
    """

    date_file_path = os.path.join(path, LAST_UPLOAD_FILENAME)

    # Check if last upload date file exists
    exists = os.path.isfile(date_file_path)
    if exists:
        # Get date from file
        with open(date_file_path, 'r') as f:
            #try:
            last_date = dateutil.parser.parse(str.strip(f.read()))
            #except

    else:
        # Set date to epoch
        last_date = datetime.utcfromtimestamp(0)

    return last_date

last_date = get_last_date(folder_path)
print("Last date: {}".format(last_date))

# Get list of files
file_list = {}
for file_path in glob.iglob(os.path.join(folder_path, '*.log')):
    head, tail = os.path.split(file_path)
    if tail != '':
        # Extract date string from filename
        if tail[1] == '-':  # Filename in format "sensor_id-ISO 8601.log"
            datepart = tail.split('-', 1)[1][:-4]
            sensor_id = tail.split('-')[0]
        else:  # Filename in format "ISO 8601.log"
            datepart = tail[:-4]
            sensor_id = '1'
        file_list[tail[:-4]] = {
            'filename': tail,
            'path': file_path,
            'sensor_id': sensor_id,
            'date': datetime.strptime(datepart, '%Y-%m-%dT%H:%M:%S')
        }

# Check for presence of any log files
if len(file_list) < 1:
    print('No .log files found in ' + folder_path)
    sys.exit()

# Filter for files with date >= last_date
file_list = {k:v for (k,v) in file_list.items() if v['date'] >= last_date}

# Check for any files to upload
if len(file_list) < 1:
    print('No new .log files to upload in ' + folder_path)
    sys.exit()

max_file_date = datetime.utcfromtimestamp(0)
# Upload log files to S3
for key, file_info in file_list.items():
    dt = file_info['date']
    object_name = 'input/' + dt.strftime('%Y/%m/%d/') + file_info['sensor_id']
    object_name += dt.strftime('-%H.csv')
    success = upload_file(file_info['path'], sensor_config.bucket_name, object_name)
    if not success:
        print('Unable to upload ' + file_info['filename'] + ' to S3!')
    else:
        print("Uploaded {}".format(file_info['filename']))
        # Update max_file_date to last uploaded file date if newer.
        #   Rrder doesn't matter, this will capture the most recent file
        #   regardless of upload order.
        if dt >= max_file_date:
            max_file_date = dt

# Write out max_file_date for next time script runs
with open(os.path.join(folder_path, LAST_UPLOAD_FILENAME), 'w') as f:
    f.write(max_file_date.isoformat())
    f.write("\n")
