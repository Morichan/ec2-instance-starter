try:
    # AWS Lambda用
    from auth.authorizer import Authorizer
except ModuleNotFoundError:
    # ローカルテスト用
    from src.auth.authorizer import Authorizer


def lambda_handler(event, context):
    """Lambda関数ハンドラー

    Lambdaトークン認証用の関数を実行する。

    Parameters
    ----------
    event: dict, required
        Lambdaプロキシ統合のための入力フォーマット
        https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        実行情報を提供するLambdaコンテキスト
        https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    -------
    Lambda認証関数の出力フォーマット: dict
        https://docs.aws.amazon.com/ja_jp/apigateway/latest/developerguide/api-gateway-lambda-authorizer-output.html
    """
    auth = Authorizer(event)

    return auth.authorize()
