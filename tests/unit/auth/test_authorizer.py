import base64

import boto3
from botocore.exceptions import ClientError
import pytest
from moto import mock_iam

with mock_iam():
    from auth.authorizer import Authorizer


@mock_iam
class TestAuthorizer:
    @pytest.fixture(scope='function', autouse=True)
    def setup(self):
        with mock_iam():
            self.iam = boto3.client('iam')
            user_name = 'valid_user'
            self.iam.create_user(UserName=user_name)
            self.iam.create_access_key(UserName=user_name)

            yield

            for user in self.iam.list_users().get('Users', []):
                self.iam.delete_user(UserName=user.get('UserName'))

    @pytest.fixture()
    def create_obj(self):
        return lambda event: Authorizer(event)

    @pytest.fixture()
    def get_user_names(self):
        return lambda: [user['UserName'] for user in self.iam.list_users().get('Users')]

    @pytest.fixture()
    def get_access_key_ids(self):
        return lambda user_name: [access_key['AccessKeyId'] for access_key in self.iam.list_access_keys(UserName=user_name).get('AccessKeyMetadata')]

    @pytest.fixture()
    def encode_token(self):
        return lambda user_name, access_key_id: 'Basic ' + base64.b64encode(f'{user_name}:{access_key_id}'.encode('utf-8')).decode('utf-8')

    def test_is_not_authorized_if_is_not_authenticated(self, create_obj, mocker):
        """認証しない場合は認可しない"""
        mocker.patch('auth.authorizer.Authorizer.authenticate', return_value=False)
        obj = create_obj({'authorizationToken': None, 'methodArn': None})

        actual = obj.authorize()

        assert actual['policyDocument']['Statement'][0]['Effect'] == 'Deny'

    def test_is_authorized_if_is_authenticated(self, create_obj, mocker):
        """認証する場合は認可する"""
        mocker.patch('auth.authorizer.Authorizer.authenticate', return_value=True)
        obj = create_obj({'authorizationToken': None, 'methodArn': None})

        actual = obj.authorize()

        assert actual['policyDocument']['Statement'][0]['Effect'] == 'Allow'

    def test_is_authenticated_if_same_access_key_and_user_name(self, create_obj, get_user_names, get_access_key_ids, encode_token):
        """同じユーザー名とアクセスキーの場合は認証する"""
        users = get_user_names()
        access_key_ids = get_access_key_ids(users[0])
        token = encode_token(users[0], access_key_ids[0])
        obj = create_obj(None)

        actual = obj.authenticate(token)

        assert actual is True

    def test_is_not_authenticated_if_not_same_access_key_and_same_user_name(self, create_obj, get_user_names, get_access_key_ids, encode_token):
        """違うユーザー名と同じアクセスキーの場合は認証しない"""
        users = get_user_names()
        access_key_ids = get_access_key_ids(users[0])
        token = encode_token('invalid_user', access_key_ids[0])
        obj = create_obj(None)

        actual = obj.authenticate(token)

        assert actual is False

    def test_is_not_authenticated_if_same_access_key_and_not_same_user_name(self, create_obj, get_user_names, get_access_key_ids, encode_token):
        """同じユーザー名と違うアクセスキーの場合は認証しない"""
        users = get_user_names()
        access_key_ids = get_access_key_ids(users[0])
        token = encode_token(users[0], '00000000000000000000')
        obj = create_obj(None)

        actual = obj.authenticate(token)

        assert actual is False

    def test_is_not_authenticated_if_not_same_access_key_and_not_same_user_name(self, create_obj, encode_token):
        """違うユーザー名と違うアクセスキーの場合は認証しない"""
        token = encode_token('invalid_user', '00000000000000000000')
        obj = create_obj(None)

        actual = obj.authenticate(token)

        assert actual is False

    def test_is_not_authenticated_if_different_access_key_and_user_name(self, create_obj, get_user_names, get_access_key_ids, encode_token):
        """ユーザー名とは別のアクセスキーの場合は認証しない"""
        self.iam.create_user(UserName='valid_user2')
        self.iam.create_access_key(UserName='valid_user2')
        users = get_user_names()
        user1_access_key_ids = get_access_key_ids(users[0])
        user2_access_key_ids = get_access_key_ids(users[1])
        user1_token = encode_token(users[0], user1_access_key_ids[0])
        user2_token = encode_token(users[1], user2_access_key_ids[0])
        cross_token = encode_token(users[0], user2_access_key_ids[0])
        obj = create_obj(None)

        actual_user1 = obj.authenticate(user1_token)
        actual_user2 = obj.authenticate(user2_token)
        actual_cross = obj.authenticate(cross_token)

        assert actual_user1 is True
        assert actual_user2 is True
        assert actual_cross is False

    def test_is_authenticated_when_has_multi_access_key(self, create_obj, get_user_names, get_access_key_ids, encode_token):
        """複数アクセスキーが存在する際は、それぞれで認証する"""
        users = get_user_names()
        self.iam.create_access_key(UserName=users[0])
        access_key_ids = get_access_key_ids(users[0])
        token1 = encode_token(users[0], access_key_ids[0])
        token2 = encode_token(users[0], access_key_ids[1])
        obj = create_obj(None)

        actual_token1 = obj.authenticate(token1)
        actual_token2 = obj.authenticate(token2)

        assert actual_token1 is True
        assert actual_token2 is True
