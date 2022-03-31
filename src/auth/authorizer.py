import base64

import boto3


iam = boto3.client('iam')


class Authorizer:
    def __init__(self, event):
        self._event = event

    def authorize(self):
        token = self._event['authorizationToken']
        method = self._event['methodArn']

        effect = 'Allow' if self.authenticate(token) else 'Deny'

        return {
            'principalId': '*',
            'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [
                    {
                        'Action': 'execute-api:Invoke',
                        'Effect': effect,
                        'Resource': method,
                    },
                ],
            },
        }

    def authenticate(self, token):
        binary_token = token.encode('utf-8')
        users = iam.list_users().get('Users', [])
        user_names = [user.get('UserName') for user in users if user.get('UserName') is not None]

        _get_access_key = lambda user_name: iam.list_access_keys(UserName=user_name).get('AccessKeyMetadata')

        _encode = lambda access_key: base64.b64encode(f'{access_key["UserName"]}:{access_key["AccessKeyId"]}'.encode('utf-8'))

        return any(b'Basic ' + _encode(key) == binary_token for name in user_names for key in _get_access_key(name))
