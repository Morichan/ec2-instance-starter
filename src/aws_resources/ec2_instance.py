import logging
from enum import Enum, auto

import boto3
from botocore.exceptions import (
    ClientError,
    ParamValidationError,
)


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class EC2Instance:
    """EC2インスタンスの状態確認と起動を管理するクラス。

    boto3を使用してEC2インスタンスの状態確認・起動を行う。

    Args:
        instance_id (str): 対象のEC2インスタンスID。
        dry_run (bool, optional): Trueの場合は実際の起動を行わない、デフォルトはFalse。

    """

    def __init__(self, instance_id, dry_run=False):
        self._state = State.UNDEFINED
        self._instance_id = instance_id
        self._dry_run = dry_run
        self._ec2 = boto3.client('ec2')
        self._describe = self._describe_instance()

    @property
    def state(self):
        """State: インスタンスの現在の状態。

        インスタンスの現在の状態を表す。
        本クラスの各種メソッドを呼出すタイミングによって自動的に変化する。

        """
        return self._state

    @property
    def instance_id(self):
        """str: 対象のEC2インスタンスID。"""
        return self._instance_id

    @property
    def dry_run(self):
        """bool: ドライランモードの場合は真を表す真偽値。"""
        return self._dry_run

    def _describe_instance(self):
        try:
            return self._ec2.describe_instances(InstanceIds=[self.instance_id])
        except ParamValidationError:
            logger.warning(f'Warning: instance_id={self.instance_id} is not string.')
            self._state = State.INSTANCE_ID_IS_NOT_STRING
            return {}
        except ClientError as e:
            self._state = self._check_state_by_client_error(e)
            return {}

    def _check_state_by_client_error(self, error_obj):
        error_code = error_obj.response['Error']['Code']

        if error_code == 'InvalidInstanceID.NotFound':
            return State.INSTANCE_ID_IS_NOT_FOUND
        else:  # pragma: no cover
            logger.exception(error_code)

    def is_already_running(self):
        """EC2インスタンスが既に起動中の場合は真を表す真偽値を返す。

        Returns:
            bool: 起動中の場合はTrue、それ以外はFalse。

        """
        self._describe = self._describe_instance()

        try:
            if not self._is_unique():
                self._state = State.INSTANCE_ID_IS_NOT_FOUND
                return False

            state_name = self._describe['Reservations'][0]['Instances'][0]['State']['Name']
            logger.info(f'EC2 Instance {self.instance_id} state is {state_name}')

            # https://docs.aws.amazon.com/ja_jp/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html
            is_running = state_name == 'running'
            if is_running:
                self._state = State.INSTANCE_IS_RUNNING
            else:
                self._state = State.INSTANCE_IS_NOT_RUNNING
            return is_running
        except KeyError:
            return False

    def _is_unique(self):
        return len(self._describe['Reservations']) == 1 and \
            len(self._describe['Reservations'][0]['Instances']) == 1

    def start(self):
        """EC2インスタンスを起動する。

        Returns:
            dict | None: boto3のstart_instancesレスポンス。ドライランの場合はNone。

        Raises:
            ClientError: インスタンスの起動に失敗した場合。
            Exception: その他の予期しないエラーが発生した場合。

        """
        try:
            return self._start_instance(self.instance_id, self.dry_run)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InsufficientInstanceCapacity':
                logger.warning(f'Warning: insufficient capacity for instance={self.instance_id}')
                self._state = State.INSUFFICIENT_CAPACITY
                raise
            logger.exception(f'Error: failed to start instance={self.instance_id}')
            self._state = State.INSTANCE_STARTING_IS_FAILED
            raise
        except:
            logger.exception(f'Error: failed to start instance={self.instance_id}')
            self._state = State.INSTANCE_STARTING_IS_FAILED
            raise

    def _start_instance(self, instance_id, dry_run):
        if dry_run:
            self._state = State.DRY_RUN
            return None
        else:
            return self._ec2.start_instances(InstanceIds=[instance_id])


class State(Enum):
    """EC2インスタンスの状態を表す列挙子。"""

    UNDEFINED = auto()
    """int: 初期状態。"""
    DRY_RUN = auto()
    """int: ドライランモードで実行した状態。"""
    INSTANCE_ID_IS_NOT_STRING = auto()
    """int: インスタンスIDが文字列でない状態。"""
    INSTANCE_ID_IS_NOT_FOUND = auto()
    """int: インスタンスIDが見つからない状態。"""
    INSTANCE_IS_NOT_RUNNING = auto()
    """int: インスタンスが起動中でない状態。"""
    INSTANCE_IS_RUNNING = auto()
    """int: インスタンスが起動中の状態。"""
    INSUFFICIENT_CAPACITY = auto()
    """int: キャパシティ不足の状態。"""
    INSTANCE_STARTING_IS_FAILED = auto()
    """int: インスタンスの起動に失敗した状態。"""
