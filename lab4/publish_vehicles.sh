#!/bin/bash

python3 emission_emulator.py --endpoint a1kaeb6ryl4498-ats.iot.us-east-1.amazonaws.com --thingName device_0 --vehicleID 0 --mode both &
python3 emission_emulator.py --endpoint a1kaeb6ryl4498-ats.iot.us-east-1.amazonaws.com --thingName device_1 --vehicleID 1 --mode both &
python3 emission_emulator.py --endpoint a1kaeb6ryl4498-ats.iot.us-east-1.amazonaws.com --thingName device_2 --vehicleID 2 --mode both &
python3 emission_emulator.py --endpoint a1kaeb6ryl4498-ats.iot.us-east-1.amazonaws.com --thingName device_3 --vehicleID 3 --mode both &
python3 emission_emulator.py --endpoint a1kaeb6ryl4498-ats.iot.us-east-1.amazonaws.com --thingName device_4 --vehicleID 4 --mode both &