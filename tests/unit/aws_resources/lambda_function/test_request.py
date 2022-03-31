import json

import pytest

import src.aws_resources.lambda_function.request as lambda_request


class TestRequest:
    @pytest.fixture()
    def create_obj(self):
        return lambda event: lambda_request.Request(event)

    def test_return_empty_if_request_body_is_None(self, create_obj, create_apigw_event):
        """リクエストボディーがNoneの場合、空辞書を返す"""
        event = create_apigw_event(None)
        obj = create_obj(event)
        expected = {}

        actual = obj.extract(event)

        assert actual == expected
        assert obj.state is lambda_request.State.BODY_IS_EMPTY
        assert obj.instance_id is None

    def test_return_empty_if_request_body_is_whitespace(self, create_obj, create_apigw_event):
        """リクエストボディーが空文字の場合、空辞書を返す"""
        event = create_apigw_event('')
        obj = create_obj(event)
        expected = {}

        actual = obj.extract(event)

        assert actual == expected
        assert obj.state is lambda_request.State.BODY_IS_EMPTY
        assert obj.instance_id is None

    def test_return_empty_if_request_body_is_not_json_string(self, create_obj, create_apigw_event):
        """リクエストボディーがJSON形式の文字列でない場合、空辞書を返す"""
        event = create_apigw_event('{')
        obj = create_obj(event)
        expected = {}

        actual = obj.extract(event)

        assert actual == expected
        assert obj.state is lambda_request.State.BODY_IS_NOT_JSON
        assert obj.instance_id is None

    def test_return_empty_if_request_body_has_not_instance_id(self, create_obj, create_apigw_event):
        """リクエストボディーがinstance_idキーを含んでいない場合、空辞書を返す"""
        event = create_apigw_event('{}')
        obj = create_obj(event)
        expected = {}

        actual = obj.extract(event)

        assert actual == expected
        assert obj.state is lambda_request.State.BODY_HAS_NOT_INSTANCE_ID
        assert obj.instance_id is None

    def test_return_dict_and_extract_instance_id_if_request_body_has_instance_id(self, create_obj, create_apigw_event):
        """リクエストボディーにinstance_idキーが存在する場合、取得した辞書を返しinstance_idを抽出する"""
        expected_instance_id = 'i-00000000000000001'
        event = create_apigw_event('{"instance_id": "i-00000000000000001"}')
        obj = create_obj(event)
        expected = {'instance_id': expected_instance_id}

        actual = obj.extract(event)

        assert actual == expected
        assert obj.state is lambda_request.State.BODY_IS_VALID
        assert obj.instance_id == expected_instance_id
