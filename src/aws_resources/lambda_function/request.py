import json
import logging
from enum import Enum, auto


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Request:
    """Lambda関数のリクエストイベントを解析するクラス。

    API Gatewayから受取ったイベントを解析し、インスタンスIDやドライランフラグを取出す。

    Args:
        event (dict): API Gatewayから受取ったイベント。

    """

    def __init__(self, event):
        self._state = State.UNDEFINED
        self._instance_id = None
        self._dry_run = False
        self.extract(event)

    @property
    def state(self):
        """State: リクエストの現在の状態。

        リクエストの現在の状態を表す。
        本クラスの各種メソッドを呼出すタイミングによって自動的に変化する。

        """
        return self._state

    @property
    def instance_id(self):
        """str: EC2インスタンスID。"""
        return self._instance_id

    @property
    def dry_run(self):
        """bool: ドライランモードの場合は真を表す真偽値。"""
        return self._dry_run

    def extract(self, event):
        """イベントからボディを取出す。

        Args:
            event (dict): API Gatewayから受取ったイベント。

        Returns:
            dict: 取出したボディ。ボディが空の場合は空のdict。

        """
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
    """リクエストの状態を表す列挙子。"""

    UNDEFINED = auto()
    """int: 初期状態。"""
    BODY_IS_EMPTY = auto()
    """int: ボディが空の状態。"""
    BODY_IS_NOT_JSON = auto()
    """int: ボディがJSON形式でない状態。"""
    BODY_HAS_NOT_INSTANCE_ID = auto()
    """int: ボディにinstance_idが含まれない状態。"""
    BODY_IS_VALID = auto()
    """int: ボディが正常に解析できた状態。"""
