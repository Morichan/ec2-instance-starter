import json
import logging
from enum import Enum, auto


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Request:
    def __init__(self, event):
        self._state = State.UNDEFINED
        self._instance_id = None
        self._dry_run = False
        self.extract(event)

    @property
    def state(self):
        return self._state

    @property
    def instance_id(self):
        return self._instance_id

    @property
    def dry_run(self):
        return self._dry_run

    def extract(self, event):
        body = {}

        if event.get('body'):
            body = self._extract_body(event)
        else:
            self._state = State.BODY_IS_EMPTY

        return body

    def _extract_body(self, event):
        body = {}

        try:
            body = json.loads(event.get('body'))
            self._instance_id = body['instance_id']
            self._dry_run = body.get('dry_run', False) is True
            self._state = State.BODY_IS_VALID
        except json.decoder.JSONDecodeError:
            self._state = State.BODY_IS_NOT_JSON
            logger.warning(f'Invalid body: {event.get("body")}')
        except KeyError:
            self._state = State.BODY_HAS_NOT_INSTANCE_ID
            logger.warning(f'Body has not instance_id: {event.get("body")}')

        return body


class State(Enum):
    UNDEFINED = auto()
    BODY_IS_EMPTY = auto()
    BODY_IS_NOT_JSON = auto()
    BODY_HAS_NOT_INSTANCE_ID = auto()
    BODY_IS_VALID = auto()
