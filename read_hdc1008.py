#!/usr/bin/env python
import smbus
import time
from utilities import error_log
from sensors.sensor_utilities import get_smbus

# select address according to jumper setting
# address  (40,41,42,43) can be found with
# sudo i2cdetect -y 1

# default address
DEVICE=0x40

def read_hdc1008(addr=DEVICE):
    bus = smbus.SMBus(get_smbus())

    # set config register
    bus.write_byte_data(addr, 0x02, 0x00)
    time.sleep(0.015) # From the data sheet

    # read temperature
    bus.write_byte(addr, 0x00)
    time.sleep(0.0625)  # From the data sheet

    # read temp data
    data0 = bus.read_byte(addr)
    data1 = bus.read_byte(addr)
    temp = ((((data0 << 8) + data1)/65536.0)*165.0) - 40.0
    time.sleep(0.015)  # From the data sheet

    # read humidity
    bus.write_byte(addr, 0x01)
    time.sleep(0.0625)  # From the data sheet
    data0 = bus.read_byte(addr)
    data1 = bus.read_byte(addr)
    humid = (((data0 << 8) + data1)/65536.0)*100.0

    return (temp, humid)

def measure_hdc1008(ts_sensor):
    try:
        fields = {}
        temperature,humidity = read_hdc1008(DEVICE)
        # ThingSpeak fields
        # Create returned dict if ts_field is defined
        if 'ts_field_temperature' in ts_sensor and isinstance(temperature, (int, float)):
            if 'offset' in ts_sensor and ts_sensor["offset"] is not None:
                temperature = temperature-ts_sensor["offset"]
            fields[ts_sensor["ts_field_temperature"]] = round(temperature, 2)
        if 'ts_field_humidity' in ts_sensor and isinstance(humidity, (int, float)):
            fields[ts_sensor["ts_field_humidity"]] = round(humidity, 2)
        return fields


    except Exception as e:
        error_log(e, 'Error: Error while reading HDC1080 Sensor. Is it connected?')
    return None


if __name__ == '__main__':
   try:

     temp,humid = read_hdc1008(DEVICE)

     print("%7.2f %7.2f" % (temp, humid))

   except (KeyboardInterrupt, SystemExit):
       pass

   except Exception as e:
       error_log(e, "Unhandled Exception in hdc1008 Measurement")
