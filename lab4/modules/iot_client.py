import boto3
import json
from typing import List


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
        with open(f"{self.output_folder}{thing_name}public.key", "w") as outfile:
            outfile.write(public_key)

        with open(f"{self.output_folder}{thing_name}private.key", "w") as outfile:
            outfile.write(private_key)

        with open(f"{self.output_folder}{thing_name}certificate.pem", "w") as outfile:
            outfile.write(certificate_pem)

        response = self.client.attach_policy(
            policyName=self.default_policy_name, target=certificate_arn
        )
        response = self.client.attach_thing_principal(
            thingName=thing_name, principal=certificate_arn
        )

    def list_things(self) -> List[str]:
        """
        Get the names of all the things in your AWS account. Should fetch things regardless
        of the thing group they are in or not.
        """
        result = []
        keep_going = True
        next_token = None
        while keep_going:
            if next_token is None:
                response = self.client.list_things()
            else:
                response = self.client.list_things(nextToken=str(next_token))
            # format is a list of dictionaries of things with thingName and other key/value pairs
            thing_names_list = response.get("things")
            for thing in thing_names_list:
                result.append(thing.get("thingName"))

            # if there is no next token, then end the loop
            next_token = response.get("nextToken")
            if next_token is None:
                keep_going = False

        return result

    """
    Set of functions in order to delete a thing with a certificate attached. Kind of involved.
    """

    # detch the certificate from the thing
    def list_thing_principals(self, thing_name: str):
        response = self.client.list_thing_principals(thingName=thing_name)
        return response.get("principals")

    def detach_certificate_from_thing(self, thing_name: str, certificate_arn: str):
        response = self.client.detach_thing_principal(
            thingName=thing_name, principal=certificate_arn
        )
        return response

    def update_certificate(self, certificate_id: str, status: str):
        response = self.client.update_certificate(
            certificateId=certificate_id, newStatus=status
        )
        return response

    def delete_certificate(self, certificate_id: str):
        response = self.client.delete_certificate(certificateId=certificate_id)
        return response

    def delete_thing(self, thing_name: str):
        response = self.client.delete_thing(thingName=thing_name)
        return response

    # detach certificate from the policy
    def list_certificate_policies(self, certificate_arn: str):
        response = self.client.list_principal_policies(principal=certificate_arn)
        return response.get("policies")

    def detach_policy_from_certificate(self, policy_name: str, certificate_arn: str):
        response = self.client.detach_policy(
            policyName=policy_name,
            target=certificate_arn
        )
        return response


    def delete_thing_with_certificate(self, thing_name: str):
        principals = self.list_thing_principals(thing_name)

        for principal in principals:
            certificate_arn = principal
            certificate_id = principal.split("/")[-1]

            # detach certificate from the policies
            policies = self.list_certificate_policies(certificate_arn = certificate_arn)
            for policy in policies:
                policy_name = policy.get("policyName")
                self.detach_policy_from_certificate(policy_name=policy_name, certificate_arn=certificate_arn)


            self.detach_certificate_from_thing(
                thing_name=thing_name, certificate_arn=certificate_arn
            )
            self.update_certificate(certificate_id=certificate_id, status="INACTIVE")
            self.delete_certificate(certificate_id=certificate_id)

        self.delete_thing(thing_name=thing_name)


if __name__ == "__main__":
    pass
