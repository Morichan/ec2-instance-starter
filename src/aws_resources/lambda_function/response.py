import json


class Response:
    def __init__(self):
        self.state = NoneState()

    @property
    def status_code(self):
        return self.state.status_code

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


class State:
    def __init__(self):
        self.check()

    @property
    def status_code(self):
        raise NotImplementedError

    @property
    def body_message(self):
        raise NotImplementedError

    def check(self):
        self._check_must_overriding_methods()

    def _check_must_overriding_methods(self):
        _ = [
            self.status_code,
            self.body_message,
        ]


class NoneState(State):
    @property
    def status_code(self):
        return 500

    @property
    def body_message(self):
        return 'Error: Internal Server Error.'


class AcceptedState(State):
    @property
    def status_code(self):
        return 202

    @property
    def body_message(self):
        return 'Accepted'


class IgnoreState(State):
    @property
    def status_code(self):
        return 200

    @property
    def body_message(self):
        return 'Ignore'


class EC2InstanceIsAlreadyRunningState(State):
    @property
    def status_code(self):
        return 409

    @property
    def body_message(self):
        return 'Error: EC2 instance is had run.'


class EC2InstanceIdIsInvalidState(State):
    @property
    def status_code(self):
        return 400

    @property
    def body_message(self):
        return 'Error: instance_id is invalid.'


class BodyHasNotInstanceIdState(State):
    @property
    def status_code(self):
        return 400

    @property
    def body_message(self):
        return 'Error: body has not instance_id.'


class BodyIsNotJsonState(State):
    @property
    def status_code(self):
        return 400

    @property
    def body_message(self):
        return 'Error: body is not JSON format.'


class BodyIsEmptyState(State):
    @property
    def status_code(self):
        return 400

    @property
    def body_message(self):
        return 'Error: body is empty.'


class StartedEC2InstanceIsFailedState(State):
    @property
    def status_code(self):
        return 500

    @property
    def body_message(self):
        return 'Error: EC2 instance was started but failed.'
