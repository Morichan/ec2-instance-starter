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
    def __init__(self, instance_id, dry_run=False):
        self._state = State.UNDEFINED
        self._instance_id = instance_id
        self._dry_run = dry_run
        self._ec2 = boto3.client('ec2')
        self._describe = self._describe_instance()

    @property
    def state(self):
        return self._state

    @property
    def instance_id(self):
        return self._instance_id

    @property
    def dry_run(self):
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
        try:
            return self._start_instance(self.instance_id, self.dry_run)
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
    UNDEFINED = auto()
    DRY_RUN = auto()
    INSTANCE_ID_IS_NOT_STRING = auto()
    INSTANCE_ID_IS_NOT_FOUND = auto()
    INSTANCE_IS_NOT_RUNNING = auto()
    INSTANCE_IS_RUNNING = auto()
    INSTANCE_STARTING_IS_FAILED = auto()
