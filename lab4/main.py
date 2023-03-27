
# custom modules
from modules import iot_client

# load environmental variables from .env file
from dotenv import load_dotenv
load_dotenv()

import os
import random
import string

# load AWS credentials
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
# load default policy name specified on AWS
DEFAULT_POLICY_NAME = os.environ.get("DEFAULT_POLICY_NAME")

if __name__ == "__main__":

    # test creation of thing via boto3
    thing_name = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(15)])

    # initialize AWS IOT client object
    iot_client = iot_client.IoTOperations(aws_access_key_id = AWS_ACCESS_KEY_ID,
        aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
        default_policy_name = DEFAULT_POLICY_NAME,
        output_folder = "./output/")

    iot_client.create_thing(thing_name = thing_name)
    