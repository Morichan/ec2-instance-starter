import json
import logging

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

        instance_id = request.body.get('instance_id')

        if self._ec2_instance.is_already_running(instance_id):
            response.body_message = 'Already running'
        else:
            result = self._ec2_instance.start_ec2_instance(instance_id)
            if not result:
                response.status_code = 404
                response.body_message = 'Error'

        return response.create_response()


class LambdaRequest:
    def __init__(self, event):
        self.body = self.extract_body(event)

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, body):
        self._body = body

    def extract_body(self, event):
        body = {}

        if event.get('body'):
            try:
                body = json.loads(event.get('body'))
            except json.decoder.JSONDecodeError:
                logger.exception(f'Invalid body: {event.get("body")}')

        return body


class LambdaResponse:
    def __init__(self):
        self.status_code = 200
        self.body_message = 'OK'

    @property
    def status_code(self):
        return self._status_code

    @status_code.setter
    def status_code(self, status_code):
        self._status_code = status_code

    @property
    def body(self):
        return json.dumps({
            "message": self.body_message,
        })

    @property
    def body_message(self):
        return self._body_message

    @body_message.setter
    def body_message(self, message):
        self._body_message = message

    def create_response(self):
        return {
            "statusCode": self.status_code,
            "body": self.body,
        }
