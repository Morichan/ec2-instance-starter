import json
import logging

from . import request as lambda_request
from . import response as lambda_response
from ..ec2_instance import EC2Instance
from ..ec2_instance import State as EC2InstanceState


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LambdaFunction:
    def __init__(self, event, context):
        self._event = event
        self._context = context

        logger.info(f'{json.dumps(self._event)}')

    def create_response(self):
        request = lambda_request.Request(self._event)
        response = lambda_response.Response()

        if request.state is lambda_request.State.BODY_IS_EMPTY:
            response.state = lambda_response.BodyIsEmptyState()
        elif request.state is lambda_request.State.BODY_IS_NOT_JSON:
            response.state = lambda_response.BodyIsNotJsonState()
        elif request.state is lambda_request.State.BODY_HAS_NOT_INSTANCE_ID:
            response.state = lambda_response.BodyHasNotInstanceIdState()
        else:
            response.state = self._analyze_state_from_ec2_instance(request.instance_id)

        return response.create_response()

    def _analyze_state_from_ec2_instance(self, instance_id):
        state = lambda_response.NoneState()
        ec2_instance = EC2Instance(instance_id)

        if ec2_instance.is_already_running():
            state = lambda_response.EC2InstanceIsAlreadyRunningState()
        else:
            if ec2_instance.state is EC2InstanceState.INSTANCE_ID_IS_NOT_STRING:
                state = lambda_response.EC2InstanceIdIsInvalidState()
            elif ec2_instance.state is EC2InstanceState.INSTANCE_ID_IS_NOT_FOUND:
                state = lambda_response.EC2InstanceIdIsInvalidState()
            else:
                result = ec2_instance.start()
                if not result:
                    state = lambda_response.StartedEC2InstanceIsFailedState()
                else:
                    state = lambda_response.AcceptedState()

        return state
