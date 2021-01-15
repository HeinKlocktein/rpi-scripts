#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.
# Modified for sensor test

import math
import threading
import time
from pprint import pprint
from time import sleep
import json

import RPi.GPIO as GPIO

from read_bme680 import measure_bme680, initBME680FromMain
from read_bme280 import measure_bme280
from read_ee895 import measure_ee895
from read_pcf8591 import measure_voltage
from read_ds18b20 import measure_temperature, filter_temperatur_values
from read_hx711 import measure_weight, compensate_temperature
from read_dht import measure_dht
from read_aht10 import measure_aht10
from read_sht31 import measure_sht31
from read_hdc1008 import measure_hdc1008
from read_max import measure_tc
from read_settings import get_settings, get_sensors
from utilities import start_single, stop_single, error_log

def measure_all_sensors(debug, filtered_temperature, ds18b20Sensors, bme680Sensors, bme680IsInitialized, dhtSensors, aht10Sensors, sht31Sensors, hdc1008Sensors, tcSensors, bme280Sensors, voltageSensors, ee895Sensors, weightSensors, hxInits):

    ts_fields = {} # dict with all fields and values which will be tranfered to ThingSpeak later
    try:

        # measure every sensor with type 0 (Ds18b20)
        try:
            for (sensorIndex, sensor) in enumerate(ds18b20Sensors):
                filter_temperatur_values(sensorIndex)
        except Exception as e:
           error_log(e, "Unhandled Exception in measure_all_sensors / ds18b20Sensors filter_temperatur_values")

        try:
            for (sensorIndex, sensor) in enumerate(ds18b20Sensors):
                if filtered_temperature is not None and len(filtered_temperature[sensorIndex]) > 0 and 'ts_field' in sensor:
                    # if we have at leat one filtered value we can upload
                    ds18b20_temperature = filtered_temperature[sensorIndex].pop()
                    if sensor["ts_field"] and ds18b20_temperature is not None:
                        if 'offset' in sensor and sensor["offset"] is not None:
                            ds18b20_temperature = ds18b20_temperature-float(sensor["offset"])
                        ds18b20_temperature = float("{0:.2f}".format(ds18b20_temperature)) # round to two decimals
                        ts_fields.update({sensor["ts_field"]: ds18b20_temperature})
                elif 'ts_field' in sensor:
                    # Case for filtered_temperature was not filled, use direct measured temperture in this case
                    ds18b20_temperature = measure_temperature(sensor)
                    if sensor["ts_field"] and ds18b20_temperature is not None:
                        if 'offset' in sensor and sensor["offset"] is not None:
                            ds18b20_temperature = ds18b20_temperature-float(sensor["offset"])
                        ds18b20_temperature = float("{0:.2f}".format(ds18b20_temperature)) # round to two decimals
                        ts_fields.update({sensor["ts_field"]: ds18b20_temperature})
        except Exception as e:
            error_log(e, "Unhandled Exception in measure_all_sensors / ds18b20Sensors")

        # measure BME680 (can only be one) [type 1]
        for (sensorIndex, bme680Sensor) in enumerate(bme680Sensors):
            if bme680IsInitialized[sensorIndex]:
                bme680_values = measure_bme680(bme680Sensor, 30)
                ts_fields.update(bme680_values)

        # measure every sensor with type 3 [DHT11/DHT22]
        for (i, sensor) in enumerate(dhtSensors):
            tempAndHum = measure_dht(sensor)
            ts_fields.update(tempAndHum)

        # measure every sensor with type 4 [MAX6675]
        for (i, sensor) in enumerate(tcSensors):
            tc_temp = measure_tc(sensor)
            ts_fields.update(tc_temp)

        # measure BME280 (can only be one) [type 5]
        if bme280Sensors and len(bme280Sensors) == 1:
            bme280_values = measure_bme280(bme280Sensors[0])
            ts_fields.update(bme280_values)

        # measure YL-40 PFC8591 (can only be one) [type 6]
        if voltageSensors and len(voltageSensors) == 1:
            voltage = measure_voltage(voltageSensors[0])
            if voltage is not None:
                ts_fields.update(voltage)

        # measure EE895 (can only be one) [type 7]
        if ee895Sensors and len(ee895Sensors) == 1:
            ee895_values = measure_ee895(ee895Sensors[0])
            if ee895_values is not None:
                ts_fields.update(ee895_values)

        # measure AHT10 (can only be one) [type 8]
        if aht10Sensors and len(aht10Sensors) == 1:
            aht10_fields = measure_aht10(aht10Sensors[0])
            if aht10_fields is not None:
                ts_fields.update(aht10_fields)

        # measure sht31 (can only be one) [type 9]
        if sht31Sensors and len(sht31Sensors) == 1:
            sht31_fields = measure_sht31(sht31Sensors[0])
            if sht31_fields is not None:
                ts_fields.update(sht31_fields)

        # measure hdc1008 (can only be one) [type 10]
        if hdc1008Sensors and len(hdc1008Sensors) == 1:
            hdc1008_fields = measure_hdc1008(hdc1008Sensors[0])
            if hdc1008_fields is not None:
                ts_fields.update(hdc1008_fields)

        # measure every sensor with type 2 [HX711]
        start_single()
        for (i, sensor) in enumerate(weightSensors):
            if hxInits is not None:
                weight = measure_weight(sensor, hxInits[i], debug)
                weight = compensate_temperature(sensor, weight, ts_fields)
                ts_fields.update(weight)
            else:
                weight = measure_weight(sensor)
                weight = compensate_temperature(sensor, weight, ts_fields)
                ts_fields.update(weight)
        stop_single()

        # print all measurement values stored in ts_fields
        if debug:
            for key, value in ts_fields.items():
                print(key + ": " + str(value))
        return ts_fields
    except Exception as ex:
        error_log(ex, "Exception during measurement 1")
        return ts_fields

def measurement():
    # dict with all fields and values which will be tranfered to ThingSpeak later
    ts_fields = {}
    try:
        # load settings
        settings = get_settings()
        # read configured sensors from settings.json
        ds18b20Sensors = get_sensors(settings, 0)
        bme680Sensors = get_sensors(settings, 1)
        weightSensors = get_sensors(settings, 2)
        dhtSensors = get_sensors(settings, 3)
        tcSensors = get_sensors(settings, 4)
        bme280Sensors = get_sensors(settings, 5)
        voltageSensors = get_sensors(settings, 6)
        ee895Sensors = get_sensors(settings, 7)
        aht10Sensors = get_sensors(settings, 8)
        sht31Sensors = get_sensors(settings, 9)
        hdc1008Sensors = get_sensors(settings, 10)
        bme680IsInitialized = {}

        # if bme680 is configured
        for (sensorIndex, bme680Sensor) in enumerate(bme680Sensors):
            bme680IsInitialized[sensorIndex] = 0
            bme680IsInitialized[sensorIndex] = initBME680FromMain(bme680Sensor)

        ts_fields = measure_all_sensors(False, None, ds18b20Sensors, bme680Sensors, bme680IsInitialized, dhtSensors, aht10Sensors, sht31Sensors, hdc1008Sensors, tcSensors, bme280Sensors, voltageSensors, ee895Sensors, weightSensors, None)
        return json.dumps(ts_fields)

    except Exception as e:
        error_log(e, "Unhandled Exception in Measurement 2")

    # Error occured
    return {}

if __name__ == '__main__':
    try:
        print(measurement())

    except (KeyboardInterrupt, SystemExit):
        pass

    except Exception as e:
        error_log(e, "Unhandled Exception in Measurement 3")
