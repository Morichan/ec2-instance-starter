from aws_resources.lambda_function import LambdaFunction


def lambda_handler(event, context):
    """Lambda関数ハンドラー

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
    Lambdaプロキシ統合のための出力フォーマット: dict
        https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    lambda_function = LambdaFunction(event, context)

    return lambda_function.create_response()
