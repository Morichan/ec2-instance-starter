import json
import logging
from enum import Enum, auto

from .ec2_instance import EC2Instance


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LambdaFunction:
    def __init__(self, event, context):
        self._event = event
        self._context = context
        self._ec2_instance = EC2Instance()

        logger.info(f'{json.dumps(self._event)}')

    def create_response(self):
        request = LambdaRequest(self._event)
        response = LambdaResponse()

        if request.state is LambdaRequestState.BODY_IS_EMPTY:
            response.state = LambdaResponseBodyIsEmptyState()
        elif request.state is LambdaRequestState.BODY_IS_NOT_JSON:
            response.state = LambdaResponseBodyIsNotJsonState()
        elif request.state is LambdaRequestState.BODY_HAS_NOT_INSTANCE_ID:
            response.state = LambdaResponseBodyHasNotInstanceIdState()
        else:
            response.state = self._analyze_state_from_ec2_instance(request.instance_id)

        return response.create_response()

    def _analyze_state_from_ec2_instance(self, instance_id):
        state = None

        try:
            if self._ec2_instance.is_already_running(instance_id):
                state = LambdaResponseEC2InstanceIsAlreadyRunningState()
            else:
                result = self._ec2_instance.start_ec2_instance(instance_id)
                if not result:
                    state = LambdaResponseStartedEC2InstanceIsFailedState()
                else:
                    state = LambdaResponseAcceptedState()
        except:
            logger.exception(f'Invalid EC2 instance ID: {instance_id}')
            state = LambdaResponseEC2InstanceIdIsInvalidState()

        return state


class LambdaRequest:
    def __init__(self, event):
        self.state = LambdaRequestState.UNDEFINED
        self.body = self.extract(event)

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, body):
        self._body = body

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state

    def extract(self, event):
        body = {}

        if event.get('body'):
            body = self._extract_body(event)
        else:
            self.state = LambdaRequestState.BODY_IS_EMPTY

        return body

    def _extract_body(self, event):
        body = {}

        try:
            body = json.loads(event.get('body'))
            self.instance_id = body['instance_id']
        except json.decoder.JSONDecodeError:
            self.state = LambdaRequestState.BODY_IS_NOT_JSON
            logger.exception(f'Invalid body: {event.get("body")}')
        except KeyError:
            self.state = LambdaRequestState.BODY_HAS_NOT_INSTANCE_ID

        return body


class LambdaRequestState(Enum):
    UNDEFINED = auto()
    BODY_IS_EMPTY = auto()
    BODY_IS_NOT_JSON = auto()
    BODY_HAS_NOT_INSTANCE_ID = auto()


class LambdaResponse:
    def __init__(self):
        self.status_code = 200
        self.body_message = 'OK'
        self.state = None

    @property
    def status_code(self):
        return self._status_code

    @status_code.setter
    def status_code(self, status_code):
        self._status_code = status_code

    @property
    def body(self):
        return json.dumps({
            "message": self.state.body_message,
        })

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state

    def create_response(self):
        return {
            "statusCode": self.state.status_code,
            "body": self.body,
        }


class LambdaResponseState:
    def __init__(self):
        self.check()

    @property
    def status_code(self):
        raise

    @property
    def body(self):
        raise

    def check(self):
        self._check_must_overriding_methods()

    def _check_must_overriding_methods(self):
        _ = [
            self.status_code,
            self.body_message,
        ]


class LambdaResponseAcceptedState(LambdaResponseState):
    def __init__(self):
        super().check()

    @property
    def status_code(self):
        return 202

    @property
    def body_message(self):
        return 'Accepted'


class LambdaResponseEC2InstanceIsAlreadyRunningState(LambdaResponseState):
    def __init__(self):
        super().check()

    @property
    def status_code(self):
        return 409

    @property
    def body_message(self):
        return 'Error: EC2 instance is had run.'


class LambdaResponseEC2InstanceIdIsInvalidState(LambdaResponseState):
    def __init__(self):
        super().check()

    @property
    def status_code(self):
        return 400

    @property
    def body_message(self):
        return 'Error: instance_id is invalid.'


class LambdaResponseBodyHasNotInstanceIdState(LambdaResponseState):
    def __init__(self):
        super().check()

    @property
    def status_code(self):
        return 400

    @property
    def body_message(self):
        return 'Error: body has not instance_id.'


class LambdaResponseBodyIsNotJsonState(LambdaResponseState):
    def __init__(self):
        super().check()

    @property
    def status_code(self):
        return 400

    @property
    def body_message(self):
        return 'Error: body is not JSON format.'


class LambdaResponseBodyIsEmptyState(LambdaResponseState):
    def __init__(self):
        super().check()

    @property
    def status_code(self):
        return 400

    @property
    def body_message(self):
        return 'Error: body is empty.'


class LambdaResponseStartedEC2InstanceIsFailedState(LambdaResponseState):
    def __init__(self):
        super().check()

    @property
    def status_code(self):
        return 500

    @property
    def body_message(self):
        return 'Error: EC2 instance was started but failed.'
