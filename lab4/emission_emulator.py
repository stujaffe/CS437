# /*
# * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# *
# * Licensed under the Apache License, Version 2.0 (the "License").
# * You may not use this file except in compliance with the License.
# * A copy of the License is located at
# *
# *  http://aws.amazon.com/apache2.0
# *
# * or in the "license" file accompanying this file. This file is distributed
# * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# * express or implied. See the License for the specific language governing
# * permissions and limitations under the License.
# */

# Substantially taken from basicDiscovery.py

# python3 emission_emulator.py --endpoint a1kaeb6ryl4498-ats.iot.us-east-1.amazonaws.com --thingName device_0 --vehicleID 0 --mode subscribe

import os
import sys
import time
import uuid
import json
import logging
import argparse
from AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider
from AWSIoTPythonSDK.core.protocol.connection.cores import ProgressiveBackOffCore
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryInvalidRequestException
from csv import DictReader
import re

"""
# General message notification callback
def customOnMessage(message):
    print("Received message on topic %s: %s\n" % (message.topic, message.payload))
"""

AllowedActions = ['both', 'publish', 'subscribe']

MAX_DISCOVERY_RETRIES = 10
GROUP_CA_PATH = "./groupCA/"

# Read in command-line parameters
parser = argparse.ArgumentParser()
parser.add_argument(
    "-e",
    "--endpoint",
    action="store",
    required=True,
    dest="host",
    help="Your AWS IoT custom endpoint",
)
parser.add_argument(
    "-n",
    "--thingName",
    action="store",
    dest="thingName",
    default="Bot",
    help="Targeted thing name",
)
parser.add_argument(
    "--vehicleID", action="store", dest="vehicleID", help="ID of vehicle (0 to 4)"
)
parser.add_argument("-m", "--mode", action="store", dest="mode", default="both",
                    help="Operation modes: %s"%str(AllowedActions))
# --print_discover_resp_only used for delopyment testing. The test run will return 0 as long as the SDK installed correctly.
parser.add_argument(
    "-p",
    "--print_discover_resp_only",
    action="store_true",
    dest="print_only",
    default=True,
)

# Parse command line arguments
args = parser.parse_args()
host = args.host
clientId = args.thingName
thingName = args.thingName
vehicle_id = args.vehicleID
print_only = args.print_only

rootCAPath = "./certificate_root/AmazonRootCA1.pem"
certificatePath = f"./certificates_things/device_{vehicle_id}.certificate.pem"
privateKeyPath = f"./certificates_things/device_{vehicle_id}.private.key"

# Publish and Subscribe topics
# The vehicles/devices will publish to topic_publish and the lambda function are subscribed to topic_publish
# The lambda function will publish to topic_subscribe and the vehicles/devices are subscribed to topic_subscribe
topic_publish = f"emissions/data/vehicle"
topic_subscribe = f"emissions/max_CO2/vehicle_{vehicle_id}"

# Get the vehicle CSV data
vehicle_data = f"./vehicle_data/vehicle{vehicle_id}.csv"


if not os.path.isfile(rootCAPath):
    parser.error("Root CA path does not exist {}".format(rootCAPath))
    exit(3)

if not os.path.isfile(certificatePath):
    parser.error("No certificate found at {}".format(certificatePath))
    exit(3)

if not os.path.isfile(privateKeyPath):
    parser.error("No private key found at {}".format(privateKeyPath))
    exit(3)

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Progressive back off core
backOffCore = ProgressiveBackOffCore()

# Discover GGCs
discoveryInfoProvider = DiscoveryInfoProvider()
discoveryInfoProvider.configureEndpoint(host)
discoveryInfoProvider.configureCredentials(rootCAPath, certificatePath, privateKeyPath)
discoveryInfoProvider.configureTimeout(10)  # 10 sec

retryCount = MAX_DISCOVERY_RETRIES if not print_only else 1
discovered = False
groupCA = None
coreInfo = None
while retryCount != 0:
    try:
        discoveryInfo = discoveryInfoProvider.discover(thingName)
        caList = discoveryInfo.getAllCas()
        coreList = discoveryInfo.getAllCores()

        # We only pick the first ca and core info
        groupId, ca = caList[0]
        coreInfo = coreList[0]
        print("Discovered GGC: %s from Group: %s" % (coreInfo.coreThingArn, groupId))

        print("Now we persist the connectivity/identity information...")
        groupCA = GROUP_CA_PATH + groupId + "_CA_" + str(uuid.uuid4()) + ".crt"
        if not os.path.exists(GROUP_CA_PATH):
            os.makedirs(GROUP_CA_PATH)
        groupCAFile = open(groupCA, "w")
        groupCAFile.write(ca)
        groupCAFile.close()

        discovered = True
        print("Now proceed to the connecting flow...")
        break
    except DiscoveryInvalidRequestException as e:
        print("Invalid discovery request detected!")
        print("Type: %s" % str(type(e)))
        print("Error message: %s" % str(e))
        print("Stopping...")
        break
    except BaseException as e:
        print("Error in discovery!")
        print("Type: %s" % str(type(e)))
        print("Error message: %s" % str(e))
        retryCount -= 1
        print("\n%d/%d retries left\n" % (retryCount, MAX_DISCOVERY_RETRIES))
        print("Backing off...\n")
        backOffCore.backOff()

if not discovered:
    # With print_discover_resp_only flag, we only woud like to check if the API get called correctly.
    if print_only:
        sys.exit(0)
    print("Discovery failed after %d retries. Exiting...\n" % (MAX_DISCOVERY_RETRIES))
    sys.exit(-1)

# Iterate through all connection options for the core and use the first successful one
myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
myAWSIoTMQTTClient.configureCredentials(groupCA, privateKeyPath, certificatePath)
#myAWSIoTMQTTClient.onMessage = customOnMessage

connected = False
for connectivityInfo in coreInfo.connectivityInfoList:
    currentHost = connectivityInfo.host
    currentPort = connectivityInfo.port
    print("Trying to connect to core at %s:%d" % (currentHost, currentPort))
    myAWSIoTMQTTClient.configureEndpoint(currentHost, currentPort)
    try:
        myAWSIoTMQTTClient.connect()
        connected = True
        break
    except BaseException as e:
        print("Error in connect!")
        print("Type: %s" % str(type(e)))
        print("Error message: %s" % str(e))

if not connected:
    print("Cannot connect to core %s. Exiting..." % coreInfo.coreThingArn)
    sys.exit(-2)


def subscribe_callback(client, userdata, message):
    print(f"Received message. Max CO2 reading for vehicle_{vehicle_id} is {message.payload}.")

def extract_numbers_from_end(input_string):
    pattern = r'\d+$'
    match = re.search(pattern, input_string)
    if match:
        return int(match.group())
    else:
        return None

# Start parsing vehicle data
print(f"Begin process for vehicle_{vehicle_id}.")

# Subscribe the vehicle/device to the lambda function max CO2 topic
if args.mode == 'both' or args.mode == 'subscribe':
    myAWSIoTMQTTClient.subscribe(topic_subscribe, 0, subscribe_callback)
    print(f"Subscribed to {topic_subscribe}")


if args.mode == 'both' or args.mode == 'publish':
    with open(vehicle_data) as f:
        dict_reader = DictReader(f)
        # each row in dict_reader is a dictionary with column names as keys and column values as values
        for row in dict_reader:
            vid = row.get("vehicle_id")
            # the vehicle_id in the CSV files is "vehx" (e.g. "veh1") so extract the numbers since the lambda function expects just the number
            vid = str(extract_numbers_from_end(vid))
            row["vehicle_id_num"] = vid
            message = json.dumps(row)
            # publish the CO2 data so the lambda function can process it
            myAWSIoTMQTTClient.publishAsync(topic_publish, message, 0)
            print(f"Action: Publish. Vehicle: vehicle_{vid}. Topic: {topic_publish}. Message: {str(message)}")
            time.sleep(1)


print(f"End process for vehicle_{vehicle_id}.")


# Block comment the basicDiscovery.py subscribing/publishing actions
"""
# Successfully connected to the core
if args.mode == 'both' or args.mode == 'subscribe':
    myAWSIoTMQTTClient.subscribe(topic, 0, None)
time.sleep(2)

loopCount = 0
while True:
    if args.mode == 'both' or args.mode == 'publish':
        message = {}
        message['message'] = args.message
        message['sequence'] = loopCount
        messageJson = json.dumps(message)
        myAWSIoTMQTTClient.publish(topic, messageJson, 0)
        if args.mode == 'publish':
            print('Published topic %s: %s\n' % (topic, messageJson))
        loopCount += 1
    time.sleep(1)
"""