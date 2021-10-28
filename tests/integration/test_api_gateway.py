import os
from unittest import TestCase

import boto3
import requests

"""
環境変数AWS_SAM_STACK_NAMEを定義することで、API Gatewayに直接テストが実行できる。
"""


class TestApiGateway(TestCase):
    api_endpoint: str

    @classmethod
    def get_stack_name(cls) -> str:
        stack_name = os.environ.get("AWS_SAM_STACK_NAME")
        if not stack_name:
            raise Exception(
                "Cannot find env var AWS_SAM_STACK_NAME. \n"
                "Please setup this environment variable with the stack name where we are running integration tests."
            )

        return stack_name

    def setUp(self) -> None:
        """環境変数AWS_SAM_STACK_NAMEを元にCloudFormation APIを利用してAPI GatewayのURLを取得する"""
        stack_name = TestApiGateway.get_stack_name()

        client = boto3.client("cloudformation")

        try:
            response = client.describe_stacks(StackName=stack_name)
        except Exception as e:
            raise Exception(
                f"Cannot find stack {stack_name}. \n" f'Please make sure stack with the name "{stack_name}" exists.'
            ) from e

        stacks = response["Stacks"]

        stack_outputs = stacks[0]["Outputs"]
        api_outputs = [output for output in stack_outputs if output["OutputKey"] == "EC2InstanceStarterApi"]
        self.assertTrue(api_outputs, f"Cannot find output HelloWorldApi in stack {stack_name}")

        self.api_endpoint = api_outputs[0]["OutputValue"]

    def test_api_gateway(self):
        response = requests.post(self.api_endpoint)
        self.assertDictEqual(response.json(), {"message": "OK"})
