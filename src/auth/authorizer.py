import base64
import os

import boto3


iam = boto3.client('iam')


class Authorizer:
    """Lambda Authorizerによる認証・認可を管理するクラス。

    IAMユーザーのアクセスキーを用いたBasic認証により、APIへのアクセス可否を判定する。
    環境変数 IS_SKIPPED を true と設定している場合、認証スキップができる（Lambda自体の実行はする）。

    """

    def __init__(self, event):
        """初期化する。

        Args:
            event (dict): API Gatewayから受取ったイベント。

        """
        self._event = event
        self._is_skipped = os.getenv('IS_SKIPPED') == 'true'

    def authorize(self):
        """認可ポリシーを生成する。

        イベントのトークンを検証し、APIへのアクセス可否を示すIAMポリシーを返す。

        Returns:
            dict: APIへのアクセス可否を示すIAMポリシー。

        """
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
        """トークンを検証し認証結果を返す。

        IAMユーザーのアクセスキーとBasic認証トークンを照合する。
        環境変数 IS_SKIPPED が true の場合は検証をスキップし、常にTrueを返す。

        Args:
            token (str): Basic認証トークン。

        Returns:
            bool: 認証に成功した場合はTrue、失敗した場合はFalse。

        """
        if self._is_skipped:
            return True

        binary_token = token.encode('utf-8')
        users = iam.list_users().get('Users', [])
        user_names = [user.get('UserName') for user in users if user.get('UserName') is not None]

        _get_access_key = lambda user_name: iam.list_access_keys(UserName=user_name).get('AccessKeyMetadata')

        _encode = lambda access_key: base64.b64encode(f'{access_key["UserName"]}:{access_key["AccessKeyId"]}'.encode('utf-8'))

        return any(b'Basic ' + _encode(key) == binary_token for name in user_names for key in _get_access_key(name))
