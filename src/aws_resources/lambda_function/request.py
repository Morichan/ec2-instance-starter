import json
import logging
from enum import Enum, auto


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Request:
    def __init__(self, event):
        self.state = State.UNDEFINED
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
            self.state = State.BODY_IS_EMPTY

        return body

    def _extract_body(self, event):
        body = {}

        try:
            body = json.loads(event.get('body'))
            self.instance_id = body['instance_id']
        except json.decoder.JSONDecodeError:
            self.state = State.BODY_IS_NOT_JSON
            logger.exception(f'Invalid body: {event.get("body")}')
        except KeyError:
            self.state = State.BODY_HAS_NOT_INSTANCE_ID

        return body


class State(Enum):
    UNDEFINED = auto()
    BODY_IS_EMPTY = auto()
    BODY_IS_NOT_JSON = auto()
    BODY_HAS_NOT_INSTANCE_ID = auto()
