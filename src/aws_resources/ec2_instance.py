import logging

import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')


class EC2Instance:
    def is_already_running(self, instance_id):
        try:
            response = ec2.describe_instances(InstanceIds=[instance_id])
            state = response['Reservations'][0]['Instances'][0]['State']['Name']
            # https://docs.aws.amazon.com/ja_jp/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html
            logger.info(f'EC2 Instance {instance_id} state is {state}')
            return state == 'running'
        except:
            logger.exception(f'Invalid EC2 instance ID: {instance_id}')
            raise

    def start_ec2_instance(self, instance_id):
        try:
            return ec2.start_instances(InstanceIds=[instance_id])
        except Exception as e:
            logger.exception(f'Invalid EC2 instance ID: {instance_id}')
