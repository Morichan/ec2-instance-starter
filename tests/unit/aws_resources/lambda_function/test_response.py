import json

import pytest

import src.aws_resources.lambda_function.response as lambda_response


@pytest.fixture()
def ok_state():
    class OkState(lambda_response.State):
        @property
        def status_code(self):
            return 200

        @property
        def body_message(self):
            return 'OK'

    return OkState()


class TestResponse:
    @pytest.fixture()
    def obj(self):
        return lambda_response.Response()

    def test_return_default_obj(self, obj):
        """初期値を返す"""
        expected_body = json.dumps({'message': 'Error: Internal Server Error.'})

        assert type(obj.state) is lambda_response.NoneState
        assert obj.status_code == 500
        assert obj.body == expected_body

    def test_return_info_for_state_if_obj_is_set_state(self, obj, ok_state):
        """状態クラスを設定する場合、設定した状態に応じた値を返す"""
        expected_body = json.dumps({'message': 'OK'})
        expected = {
            'statusCode': 200,
            'body': expected_body,
        }

        obj.state = ok_state
        actual = obj.create_response()

        assert obj.status_code == 200
        assert obj.body == expected_body
        assert actual == expected


class TestState:
    def test_raise_error_if_obj_is_created(self):
        """素のオブジェクトを作成する場合、例外を投げる"""

        with pytest.raises(RuntimeError):
            obj = lambda_response.State()

    def test_raise_error_if_obj_is_overrided_status_code_only(self):
        """素のオブジェクトから継承してstatus_codeプロパティのみ上書きする場合、例外を投げる"""
        class InsufficientState(lambda_response.State):
            @property
            def status_code(self):
                pass

        with pytest.raises(RuntimeError):
            obj = InsufficientState()

    def test_ok_if_obj_is_overrided(self):
        """素のオブジェクトから継承して適切なプロパティを上書きする場合、正常なオブジェクトを作成する"""
        expected_status_code = 200
        expected_body_message = 'OK'
        class EnoughState(lambda_response.State):
            @property
            def status_code(self):
                return 200

            @property
            def body_message(self):
                return 'OK'

        obj = EnoughState()

        assert obj.status_code == expected_status_code
        assert obj.body_message == expected_body_message
