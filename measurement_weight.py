#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

from read_hx711 import measure_weight
from utilities import start_single, stop_single, blockPrinting, error_log
import sys
import json


@blockPrinting
def get_weight():
    weight_sensor = {}
    weight_sensor["pin_dt"] = int(sys.argv[1])
    weight_sensor["pin_sck"] = int(sys.argv[2])
    weight_sensor["channel"] = sys.argv[3]
    weight_sensor["offset"] = 0
    weight_sensor["reference_unit"] = 1
    start_single()
    weight = measure_weight(weight_sensor)
    stop_single()

    return json.dumps(weight)


if __name__ == '__main__':
    try:
        print(get_weight())

    except (KeyboardInterrupt, SystemExit):
        pass

    except Exception as e:
        error_log(e, "Unhandled Exception in Measurement")
