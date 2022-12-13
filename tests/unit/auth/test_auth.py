import json

import boto3
from moto import mock_iam

with mock_iam():
    import auth


@mock_iam
def test_allow_if_valid_auth_info_is_sent(create_apigw_event, mocker):
    """有効な認証情報を送信する場合、認可する"""
    mocker.patch('auth.authorizer.Authorizer.authenticate', return_value=True)
    iam = boto3.client('iam')
    valid_overrided_event = {'authorizationToken': 'valid_token', 'methodArn': 'valid_arn_string'}

    response = auth.lambda_handler({**create_apigw_event({}), **valid_overrided_event}, '')

    assert response['policyDocument']['Statement'][0]['Effect'] == 'Allow'


@mock_iam
def test_deny_if_invalid_auth_info_is_sent(create_apigw_event, mocker):
    """無効な認証情報を送信する場合、認可しない"""
    mocker.patch('auth.authorizer.Authorizer.authenticate', return_value=False)
    iam = boto3.client('iam')
    valid_overrided_event = {'authorizationToken': 'valid_token', 'methodArn': 'valid_arn_string'}

    response = auth.lambda_handler({**create_apigw_event({}), **valid_overrided_event}, '')

    assert response['policyDocument']['Statement'][0]['Effect'] == 'Deny'
