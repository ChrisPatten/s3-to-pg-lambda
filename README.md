# Reading Temperature and Humidity Sensors to send to RDS
This project uses Raspberry Pi (or other Python-capable computer with GPIO)
to capture readings from DHT11 or DS18B20 sensors, upload the data to AWS S3,
process those readings to calculate dew point and convert to Fahrenheit, and
insert the readings into a Postgres database.

## Hardware
**Add hardware details here**

## Embedded Software
Ensure Python 3 and cron are available on the device. Cron is used to call the
`get_reading.py` script every 10 seconds to take a reading and store the result
in a file. Files are split by the hour with filename format `<sensor_id>-%Y-%m-%dT%H:00:00.log`.
All timestamps are UTC.

Additionally, the uploader requires the `boto3` library.

### DHT11 Requirements
Reading from the DHT11 requires the `RPi.GPIO` library.

### DS18B20 Requirements
Reading from the DS18B20 requires 1-Wire capable hardware. Using a NextThingCo
CHIP, check for the necessary kernel extension:

```
$ sudo cat /sys/kernel/debug/pinctrl/1c20800.pinctrl/pinmux-pins | grep onewire
pin 98 (PD2): onewire 1c20800.pinctrl:98 function gpio_in group PD2
```

Check to make sure it's functioning by:

```
$ sudo modprobe w1_therm
$ ls /sys/bus/w1/devices/
<28-############> w1_bus_master1
$ cat /sys/bus/w1/devices/<28-############>/w1_slave
30 00 4b 46 ff ff 0f 10 b8 : crc=b8 YES
30 00 4b 46 ff ff 0f 10 b8 t=23812
```

In this example, temperature is represented by `t=23812`, with the value being
temperature in C * 1000 (e.g. 23.812&deg;C)

### Uploader
The uploader script looks for a file called `last_upload_date.txt` in the log
directory containing an ISO 8601 format (YYYY-MM-DDTHH:MM:SS) string as its
only contents. If no file is found it will upload all of the log files.
If that file is found it will upload all files whose filename dates are on or after
that datetime.

### Setup
1. Copy `get_reading.py`, `dht11.py`, and `upload_files.py` to the base directory
you want to use
1. Update the values in `sensor_config.sample.py` and save as `sensor_config.py`
1. Create a folder `./logs` in that directory
1. Run `chmod +x` for each of the three scripts to allow them to be executed
1. Update the variables in the provided crontab to match the base directory and chosen `SENSOR_ID`

## AWS Lambda
Update the values in `rds_config.sample.py` and save as `rds_config.py`.
Package the Lambda function by executing `package.sh`. This script zips `app.py`
along with the dependencies from the `s3pglambda` folder into a file called `deploy.zip`
which can then be uploaded to Lambda.