import json
import logging

import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')


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

    logger.info(f'{json.dumps(event)}')

    request_body = {}
    status_code = 200
    body_message = 'OK'

    if event.get('body'):
        try:
            request_body = json.loads(event.get('body'))
        except json.decoder.JSONDecodeError:
            logger.exception(f'Invalid body: {event.get("body")}')

    instance_id = request_body.get('instance_id')

    if _is_already_running(instance_id):
        body_message = 'Already running'
    else:
       result = _start_ec2_instance(instance_id)
       if not result:
           status_code = 404
           body_message = 'Error'

    return {
        "statusCode": status_code,
        "body": json.dumps({
            "message": body_message,
        }),
    }


def _is_already_running(instance_id):
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        state = response['Reservations'][0]['Instances'][0]['State']['Name']
        # https://docs.aws.amazon.com/ja_jp/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html
        logger.info(f'EC2 Instance {instance_id} state is {state}')
        return state == 'running'
    except:
        logger.exception(f'Invalid EC2 instance ID: {instance_id}')


def _start_ec2_instance(instance_id):
    try:
        return ec2.start_instances(InstanceIds=[instance_id])
    except Exception as e:
        logger.exception(f'Invalid EC2 instance ID: {instance_id}')
