import boto3
from botocore.exceptions import ClientError
import pytest
from moto import mock_ec2
from moto.ec2.models import AMIS

from src.aws_resources.ec2_instance import EC2Instance
from src.aws_resources.ec2_instance import State


@mock_ec2
class TestEC2Instance:
    @pytest.fixture()
    def create_obj(self):
        return lambda instance_id: EC2Instance(instance_id)

    def test_return_default_obj(self, create_obj):
        """初期値を返す"""
        obj = create_obj(None)

        assert obj.instance_id == None

    def test_instance_id_is_not_string_if_instance_id_be_None_is_set(self, create_obj):
        """インスタンスIDがNoneの場合、instance_idは文字列でないことを確認できる"""
        obj = create_obj(None)

        actual = obj.is_already_running()

        assert actual is False
        assert obj.state == State.INSTANCE_ID_IS_NOT_STRING

    def test_instance_id_is_not_string_if_instance_id_be_uninfo_number_is_set(self, create_obj):
        """インスタンスIDが無意味な数字の場合、instance_idは文字列でないことを確認できる"""
        obj = create_obj(1234)

        actual = obj.is_already_running()

        assert actual is False
        assert obj.state == State.INSTANCE_ID_IS_NOT_STRING

    def test_instance_id_is_not_found_if_instance_id_be_whitespace_is_set(self, create_obj):
        """インスタンスIDが空文字の場合、instance_idを持つインスタンスは見つからない"""
        obj = create_obj('')

        actual = obj.is_already_running()

        assert actual is False
        assert obj.state == State.INSTANCE_ID_IS_NOT_FOUND

    def test_instance_id_is_not_found_if_instance_id_is_not_unique(self, create_obj, mocker):
        """インスタンスIDが一意に定まらない場合、instance_idを持つインスタンスは見つからない"""
        mocker.patch('src.aws_resources.ec2_instance.EC2Instance._is_unique', return_value=False)
        obj = create_obj('')

        actual = obj.is_already_running()

        assert actual is False
        assert obj.state == State.INSTANCE_ID_IS_NOT_FOUND

    def test_check_instance_is_not_running(self, create_obj):
        """インスタンスが起動していないことを確認できる"""
        ec2 = boto3.client('ec2', region_name='ap-northeast-1')
        ec2.run_instances(ImageId=AMIS[0]['ami_id'], MinCount=2, MaxCount=2)
        all_instance_info = ec2.describe_instances()
        instance_id = all_instance_info['Reservations'][0]['Instances'][0]['InstanceId']
        ec2.stop_instances(InstanceIds=[instance_id])
        obj = create_obj(instance_id)

        actual = obj.is_already_running()

        assert actual is False
        assert obj.state == State.INSTANCE_IS_NOT_RUNNING

    def test_check_instance_is_running(self, create_obj):
        """インスタンスが起動していることを確認できる"""
        ec2 = boto3.client('ec2', region_name='ap-northeast-1')
        ec2.run_instances(ImageId=AMIS[0]['ami_id'], MinCount=2, MaxCount=2)
        all_instance_info = ec2.describe_instances()
        instance_id = all_instance_info['Reservations'][0]['Instances'][0]['InstanceId']
        ec2.start_instances(InstanceIds=[instance_id])
        obj = create_obj(instance_id)

        actual = obj.is_already_running()

        assert actual is True
        assert obj.state == State.INSTANCE_IS_RUNNING

    def test_start_instance(self, create_obj):
        """インスタンスが起動できる"""
        ec2 = boto3.client('ec2', region_name='ap-northeast-1')
        ec2.run_instances(ImageId=AMIS[0]['ami_id'], MinCount=2, MaxCount=2)
        all_instance_info = ec2.describe_instances()
        instance_id = all_instance_info['Reservations'][0]['Instances'][0]['InstanceId']
        obj = create_obj(instance_id)

        actual = obj.start()

        assert actual['ResponseMetadata']['HTTPStatusCode'] == 200

    def test_raise_error_if_instance_starting_is_failed(self, create_obj, mocker):
        """インスタンスの起動に失敗した場合、例外を投げる"""
        mocker.patch('src.aws_resources.ec2_instance.EC2Instance._start_instance', side_effect=Exception())
        obj = create_obj(None)

        with pytest.raises(Exception):
            obj.start()

        assert obj.state == State.INSTANCE_STARTING_IS_FAILED
