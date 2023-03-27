import boto3
import json


class IoTOperations(object):
    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        default_policy_name: str,
        output_folder: str,
    ) -> None:
        self.client = boto3.client("iot")
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.default_policy_name = default_policy_name
        self.output_folder = output_folder

    def create_thing(self, thing_name: str) -> None:
        response = self.client.create_thing(thingName=thing_name)
        response_data = json.loads(json.dumps(response, sort_keys=False, indent=4))

        for element in response_data:
            if element == "thingArn":
                thingArn = response_data["thingArn"]
            elif element == "thingId":
                thingId = response_data["thingId"]
                self.create_certificate(thing_name=thing_name)

    def create_certificate(self, thing_name: str):
        response = self.client.create_keys_and_certificate(setAsActive=True)
        response_data = json.loads(json.dumps(response, sort_keys=False, indent=4))

        for element in response_data:
            if element == "certificateArn":
                certificate_arn = response_data["certificateArn"]
            elif element == "keyPair":
                public_key = response_data["keyPair"]["PublicKey"]
                private_key = response_data["keyPair"]["PrivateKey"]
            elif element == "certificatePem":
                certificate_pem = response_data["certificatePem"]
            elif element == "certificateId":
                certificate_id = response_data["certificateId"]

        # save keys/pems/etc to files
        with open(f"{self.output_folder}public.key", "w") as outfile:
            outfile.write(public_key)

        with open(f"{self.output_folder}private.key", "w") as outfile:
            outfile.write(private_key)

        with open(f"{self.output_folder}cert.pem", "w") as outfile:
            outfile.write(certificate_pem)

        response = self.client.attach_policy(
            policyName=self.default_policy_name, target=certificate_arn
        )
        response = self.client.attach_thing_principal(
            thingName=thing_name, principal=certificate_arn
        )


if __name__ == "__main__":
    pass
