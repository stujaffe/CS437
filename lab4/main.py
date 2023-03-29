# custom modules
from modules import iot_client

# load environmental variables from .env file
from dotenv import load_dotenv

load_dotenv()

import os

# load AWS credentials
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
# load default policy name specified on AWS
DEFAULT_POLICY_NAME = os.environ.get("DEFAULT_POLICY_NAME")

# number of IoT things to create
NUM_THINGS = 5

# do you want to delete all the current things?
DELETE_THINGS = True

# GreenGrass group name
GROUP_NAME = "Greengrass_Lab4"

if __name__ == "__main__":
    # initialize AWS IOT client object
    iot_client = iot_client.IoTOperations(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        default_policy_name=DEFAULT_POLICY_NAME,
        output_folder="./certificates/",
    )

    if DELETE_THINGS:
        thing_names = iot_client.list_things()

        for name in thing_names:
            iot_client.delete_thing_with_certificate(thing_name=name)


    # create IoT things
    for i in range(NUM_THINGS):
        thing_name = f"device_{i}"
        iot_client.create_thing(thing_name=thing_name)
    
    # add to group
    for name in iot_client.list_things():
        iot_client.add_thing_to_group(thing_name=name, group_name=GROUP_NAME)



    
