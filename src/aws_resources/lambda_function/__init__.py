import json
import logging

from . import request as lambda_request
from . import response as lambda_response
from ..ec2_instance import EC2Instance


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LambdaFunction:
    def __init__(self, event, context):
        self._event = event
        self._context = context
        self._ec2_instance = EC2Instance()

        logger.info(f'{json.dumps(self._event)}')

    def create_response(self):
        request = lambda_request.LambdaRequest(self._event)
        response = lambda_response.LambdaResponse()

        if request.state is lambda_request.LambdaRequestState.BODY_IS_EMPTY:
            response.state = lambda_response.LambdaResponseBodyIsEmptyState()
        elif request.state is lambda_request.LambdaRequestState.BODY_IS_NOT_JSON:
            response.state = lambda_response.LambdaResponseBodyIsNotJsonState()
        elif request.state is lambda_request.LambdaRequestState.BODY_HAS_NOT_INSTANCE_ID:
            response.state = lambda_response.LambdaResponseBodyHasNotInstanceIdState()
        else:
            response.state = self._analyze_state_from_ec2_instance(request.instance_id)

        return response.create_response()

    def _analyze_state_from_ec2_instance(self, instance_id):
        state = None

        try:
            if self._ec2_instance.is_already_running(instance_id):
                state = lambda_response.LambdaResponseEC2InstanceIsAlreadyRunningState()
            else:
                result = self._ec2_instance.start_ec2_instance(instance_id)
                if not result:
                    state = lambda_response.LambdaResponseStartedEC2InstanceIsFailedState()
                else:
                    state = lambda_response.LambdaResponseAcceptedState()
        except:
            logger.exception(f'Invalid EC2 instance ID: {instance_id}')
            state = lambda_response.LambdaResponseEC2InstanceIdIsInvalidState()

        return state
