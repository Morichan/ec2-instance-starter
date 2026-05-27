import json


class Response:
    """Lambda関数のレスポンスを生成するクラス。

    設定された状態に基づき、HTTPステータスコードとボディを含むレスポンスを生成する。

    """

    def __init__(self):
        self.state = NoneState()

    @property
    def status_code(self):
        """int: HTTPステータスコード。"""
        return self.state.status_code

    @property
    def body(self):
        """str: JSONシリアライズしたレスポンスボディ。"""
        return json.dumps({
            "message": self.state.body_message,
        })

    @property
    def state(self):
        """State: レスポンスの現在の状態。初期値はNoneState。"""
        return self._state

    @state.setter
    def state(self, state):
        self._state = state

    def create_response(self):
        """Lambdaレスポンスを生成する。

        Returns:
            dict: HTTPステータスコードとボディを含むレスポンス。
                {
                    "statusCode": int,
                    "body": str
                }

        """
        return {
            "statusCode": self.state.status_code,
            "body": self.body,
        }


class State:
    """レスポンスの状態を表す基底クラス。

    具象クラスは status_code と body_message を必ずオーバーライドする必要がある。
    オブジェクト生成時に上記がオーバーライドされているか確認する。

    Raises:
        NotImplementedError: 実装必須プロパティが実装されていない場合。

    """

    def __init__(self):
        self.check()

    @property
    def status_code(self):
        """int: HTTPステータスコード。"""
        raise NotImplementedError

    @property
    def body_message(self):
        """str: レスポンスボディに設定する文字列。"""
        raise NotImplementedError

    def check(self):
        """実装必須メソッドが正常に実装されているかチェックする。

        Raises:
            NotImplementedError: 実装必須プロパティが実装されていない場合。

        """
        self._check_must_overriding_methods()

    def _check_must_overriding_methods(self):
        _ = [
            self.status_code,
            self.body_message,
        ]


class NoneState(State):
    """状態未設定時のデフォルト状態 (500: Internal Server Error)。

    予期しないエラーとなった場合に返す可能性がある。

    """

    @property
    def status_code(self):
        return 500

    @property
    def body_message(self):
        return 'Error: Internal Server Error.'


class AcceptedState(State):
    """EC2インスタンスの起動を受付けた状態 (202: Accepted)。

    EC2インスタンスの起動リクエストを正常に受付けた場合に返す。

    """

    @property
    def status_code(self):
        return 202

    @property
    def body_message(self):
        return 'Accepted'


class IgnoreState(State):
    """ドライランモードで実行した状態 (200: OK)。

    ドライランモードで実行したため、実際の起動を行わなかった場合に返す。

    """

    @property
    def status_code(self):
        return 200

    @property
    def body_message(self):
        return 'Ignore'


class EC2InstanceIsAlreadyRunningState(State):
    """EC2インスタンスが既に起動中の状態 (409: Conflict)。

    起動リクエスト時にEC2インスタンスが既に起動中だった場合に返す。

    """

    @property
    def status_code(self):
        return 409

    @property
    def body_message(self):
        return 'Error: EC2 instance is had run.'


class EC2InstanceIdIsInvalidState(State):
    """EC2インスタンスIDが無効な状態 (400: Bad Request)。

    インスタンスIDが文字列でない、または対象のEC2インスタンスが存在しない場合に返す。

    """

    @property
    def status_code(self):
        return 400

    @property
    def body_message(self):
        return 'Error: instance_id is invalid.'


class BodyHasNotInstanceIdState(State):
    """リクエストボディにinstance_idが含まれない状態 (400: Bad Request)。

    受取ったリクエストボディのJSONにinstance_idキーが存在しない場合に返す。

    """

    @property
    def status_code(self):
        return 400

    @property
    def body_message(self):
        return 'Error: body has not instance_id.'


class BodyIsNotJsonState(State):
    """リクエストボディがJSON形式でない状態 (400: Bad Request)。

    受取ったリクエストボディのパースに失敗した場合に返す。

    """

    @property
    def status_code(self):
        return 400

    @property
    def body_message(self):
        return 'Error: body is not JSON format.'


class BodyIsEmptyState(State):
    """リクエストボディが空の状態 (400: Bad Request)。

    受取ったリクエストにボディが存在しない場合に返す。

    """

    @property
    def status_code(self):
        return 400

    @property
    def body_message(self):
        return 'Error: body is empty.'


class InsufficientCapacityState(State):
    """EC2インスタンスのキャパシティが不足している状態 (503: Service Unavailable)。

    EC2インスタンスの起動時にインスタンスタイプのキャパシティ不足が発生した場合に返す。

    """

    @property
    def status_code(self):
        return 503

    @property
    def body_message(self):
        return 'Error: EC2 insufficient capacity. Please try again later.'


class StartedEC2InstanceIsFailedState(State):
    """EC2インスタンスの起動に失敗した状態 (500: Internal Server Error)。

    EC2インスタンスの起動処理中に予期しないエラーが発生した場合に返す。

    """

    @property
    def status_code(self):
        return 500

    @property
    def body_message(self):
        return 'Error: EC2 instance was started but failed.'
