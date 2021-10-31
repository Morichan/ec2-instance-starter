import json
from unittest import TestCase
from unittest.mock import MagicMock

import boto3
import pytest
from moto import mock_ec2
from moto.ec2.models import AMIS

from src import app


@pytest.fixture()
def create_apigw_event():
    """API Gatewayが生成するイベントオブジェクトを生成する"""
    def factory(body_text):
        return {
            "body": body_text,
            "resource": "/{proxy+}",
            "requestContext": {
                "resourceId": "123456",
                "apiId": "1234567890",
                "resourcePath": "/{proxy+}",
                "httpMethod": "POST",
                "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
                "accountId": "123456789012",
                "identity": {
                    "apiKey": "",
                    "userArn": "",
                    "cognitoAuthenticationType": "",
                    "caller": "",
                    "userAgent": "Custom User Agent String",
                    "user": "",
                    "cognitoIdentityPoolId": "",
                    "cognitoIdentityId": "",
                    "cognitoAuthenticationProvider": "",
                    "sourceIp": "127.0.0.1",
                    "accountId": "",
                },
                "stage": "prod",
            },
            "queryStringParameters": {"foo": "bar"},
            "headers": {
                "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
                "Accept-Language": "en-US,en;q=0.8",
                "CloudFront-Is-Desktop-Viewer": "true",
                "CloudFront-Is-SmartTV-Viewer": "false",
                "CloudFront-Is-Mobile-Viewer": "false",
                "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
                "CloudFront-Viewer-Country": "US",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Upgrade-Insecure-Requests": "1",
                "X-Forwarded-Port": "443",
                "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
                "X-Forwarded-Proto": "https",
                "X-Amz-Cf-Id": "aaaaaaaaaae3VYQb9jd-nvCd-de396Uhbp027Y2JvkCPNLmGJHqlaA==",
                "CloudFront-Is-Tablet-Viewer": "false",
                "Cache-Control": "max-age=0",
                "User-Agent": "Custom User Agent String",
                "CloudFront-Forwarded-Proto": "https",
                "Accept-Encoding": "gzip, deflate, sdch",
            },
            "pathParameters": {"proxy": "/examplepath"},
            "httpMethod": "POST",
            "stageVariables": {"baz": "qux"},
            "path": "/examplepath",
        }
    return factory


@mock_ec2
def test_respond_ok_if_valid_instance_id_is_sent(create_apigw_event, mocker):
    """有効なインスタンスIDを送信する場合、OKを返す"""
    ec2 = boto3.client('ec2', region_name='ap-northeast-1')
    ec2.run_instances(ImageId=AMIS[0]['ami_id'], MinCount=2, MaxCount=2)
    all_instance_info = ec2.describe_instances()
    instance_id = all_instance_info['Reservations'][0]['Instances'][0]['InstanceId']
    ec2.stop_instances(InstanceIds=[instance_id])
    body_with_valid_instance_id = f'{{"instance_id": "{instance_id}"}}'

    ret = app.lambda_handler(create_apigw_event(body_with_valid_instance_id), '')
    data = json.loads(ret['body'])

    assert ret['statusCode'] == 202
    assert 'message' in ret['body']
    assert data['message'] == 'Accepted'


@mock_ec2
def test_respond_error_if_invalid_instance_id_is_sent(create_apigw_event, mocker):
    """無効なインスタンスIDを送信する場合、エラーを返す"""
    body_with_invalid_instance_id = '{"instance_id": "i-00000000000000000"}'
    ret = app.lambda_handler(create_apigw_event(body_with_invalid_instance_id), '')
    data = json.loads(ret['body'])

    assert ret['statusCode'] == 400
    assert 'message' in ret['body']
    assert data['message'] == 'Error: instance_id is invalid.'


@mock_ec2
def test_respond_error_if_instance_id_is_not_found(create_apigw_event, mocker):
    """存在しないインスタンスIDを送信する場合、エラーを返す"""
    body_with_not_found_instance_id = '{"instance_id": "i-00000000000000001"}'
    ret = app.lambda_handler(create_apigw_event(body_with_not_found_instance_id), '')
    data = json.loads(ret['body'])

    assert ret['statusCode'] == 400
    assert 'message' in ret['body']
    assert data['message'] == 'Error: instance_id is invalid.'


@mock_ec2
def test_respond_error_if_body_without_instance_id(create_apigw_event, mocker):
    """インスタンスID無しのbodyを送信する場合、エラーを返す"""
    body_without_instance_id = '{"data": "is not instance_id"}'
    ret = app.lambda_handler(create_apigw_event(body_without_instance_id), '')
    data = json.loads(ret['body'])

    assert ret['statusCode'] == 400
    assert 'message' in ret['body']
    assert data['message'] == 'Error: body has not instance_id.'


@mock_ec2
def test_respond_error_if_body_is_invalid_json(create_apigw_event, mocker):
    """JSON形式でないbodyを送信する場合、エラーを返す"""
    not_json_body = 'This is not JSON string.'
    ret = app.lambda_handler(create_apigw_event(not_json_body), '')
    data = json.loads(ret['body'])

    assert ret['statusCode'] == 400
    assert 'message' in ret['body']
    assert data['message'] == 'Error: body is not JSON format.'


@mock_ec2
def test_respond_error_if_body_is_whitespace(create_apigw_event, mocker):
    """空文字bodyを送信する場合、エラーを返す"""
    ret = app.lambda_handler(create_apigw_event(''), '')
    data = json.loads(ret['body'])

    assert ret['statusCode'] == 400
    assert 'message' in ret['body']
    assert data['message'] == 'Error: body is empty.'


@mock_ec2
def test_respond_error_if_body_is_not_found(create_apigw_event, mocker):
    """body無しで送信する場合、エラーを返す"""
    ret = app.lambda_handler(create_apigw_event(None), '')
    data = json.loads(ret['body'])

    assert ret['statusCode'] == 400
    assert 'message' in ret['body']
    assert data['message'] == 'Error: body is empty.'


@mock_ec2
def test_respond_error_if_ec2_instance_is_had_run(create_apigw_event, mocker):
    """既にEC2インスタンスが起動している場合、エラーを返す"""
    ec2 = boto3.client('ec2', region_name='ap-northeast-1')
    ec2.run_instances(ImageId=AMIS[0]['ami_id'], MinCount=2, MaxCount=2)
    all_instance_info = ec2.describe_instances()
    instance_id = all_instance_info['Reservations'][0]['Instances'][0]['InstanceId']
    body_with_valid_instance_id = f'{{"instance_id": "{instance_id}"}}'

    ret = app.lambda_handler(create_apigw_event(body_with_valid_instance_id), '')
    data = json.loads(ret['body'])

    assert ret['statusCode'] == 409
    assert 'message' in ret['body']
    assert data['message'] == 'Error: EC2 instance is had run.'


@mock_ec2
def test_respond_error_if_started_ec2_instance_is_failed(create_apigw_event, mocker):
    """EC2インスタンスの起動に場合、エラーを返す"""
    mocker.patch('src.aws_resources.lambda_function.EC2Instance.start', return_value=None)
    ec2 = boto3.client('ec2', region_name='ap-northeast-1')
    ec2.run_instances(ImageId=AMIS[0]['ami_id'], MinCount=2, MaxCount=2)
    all_instance_info = ec2.describe_instances()
    instance_id = all_instance_info['Reservations'][0]['Instances'][0]['InstanceId']
    ec2.stop_instances(InstanceIds=[instance_id])
    body_with_valid_instance_id = f'{{"instance_id": "{instance_id}"}}'

    ret = app.lambda_handler(create_apigw_event(body_with_valid_instance_id), '')
    data = json.loads(ret['body'])

    assert ret['statusCode'] == 500
    assert 'message' in ret['body']
    assert data['message'] == 'Error: EC2 instance was started but failed.'
