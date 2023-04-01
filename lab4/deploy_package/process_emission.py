import json
import logging
import sys

import greengrasssdk

# Logging
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# SDK Client
client = greengrasssdk.client("iot-data")

# Dictionary to hold the vehicle max emission data
vehicle_emissions = {}

NUM_VEHICLES = 5
for i in range(NUM_VEHICLES):
    vehicle_emissions["vehicle_{}".format(i)] = 0


# Counter
my_counter = 0


def lambda_handler(event, context):
    global my_counter
    global vehicle_emissions

    assert "vehicle_id" in event, "Missing vehicle_id in event"
    assert "vehicle_CO2" in event, "Missing vehicle_CO2 in event"

    try:
        # TODO1: Get your data
        # vehicle id
        vehicle_id = event.get("vehicle_id")
        vehicle_data = event.get("vehicle_CO2")

        # Check if the required data is available
        if vehicle_id is None or vehicle_data is None:
            logger.error("Missing vehicle_id or vehicle_CO2 in the event")
            return

        # TODO2: Calculate max CO2 emission
        # get the max emissions for this vehicle_id
        vehicle_emissions["vehicle_{}".format(vehicle_id)] = max(
            float(vehicle_data), float(vehicle_emissions.get("vehicle_{}".format(vehicle_id), 0))
        )

        # TODO3: Return the result
        # result for all the vehicles
        client.publish(
            topic="emissions/max_CO2/vehicle_{}".format(vehicle_id),
            payload=json.dumps(
                {
                    "message": "Max CO2 emissions.",
                    "vehicle_id": vehicle_id,
                    "counter": my_counter,
                    "max_CO2": vehicle_emissions.get("vehicle_{}".format(vehicle_id), -999),
                }
            ),
        )

        my_counter += 1

    except Exception as e:
        logger.error("An error occurred: {}".format(e))

    return