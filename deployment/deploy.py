import os
import boto3
import zipfile
import subprocess
import shlex
from botocore.exceptions import ClientError


def configure_aws_credentials():
    # Check for other means of providing credentials before using profile
    if 'AWS_ACCESS_KEY_ID' not in os.environ:
        os.environ['AWS_PROFILE'] = 'default'

def check_dynamodb_exists():
    # Configure AWS credentials from profile
    configure_aws_credentials()
    dynamodb_client = boto3.client('dynamodb', region_name="us-east-1")
    table_name = 'XXX-start-stop'
    try:
        dynamodb_client.describe_table(
            TableName=table_name
        )
        print('DynamoDB table: ' + table_name + ' exists')
    except ClientError as err:
        if err.response['Error']['Code'] != 'ResourceNotFoundException':
            raise
        print('Creating DynamoDB table: ' + table_name + '...')
        dynamodb_client.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'LockID',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'LockID',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            SSESpecification={
                'Enabled': True
            },
            Tags=[
                {
                    'Key': 'moniker',
                    'Value': 'moniker'
                },
                {
                    'Key': 'owner_name',
                    'Value': 'XXX_owner'
                },
                {
                    'Key': 'group_name',
                    'Value': 'XXX_group'
                }
            ]

        )
        waiter = dynamodb_client.get_waiter('table_exists')
        waiter.wait(
            TableName=table_name,
            WaiterConfig={
                'Delay': 5,
                'MaxAttempts': 10
            }
        )

def command_execution(cmd, cwd=None):
    command = shlex.split(cmd)
    retval = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=cwd)
    while True:
        line = retval.stdout.readline().rstrip()
        print(line)
        if not line and retval.poll() is not None:
            break
    if retval.returncode != 0:
        raise subprocess.CalledProcessError(retval.returncode, cmd)

def create_resources():
    check_dynamodb_exists()
    command_execution('terraform init')
    command_execution('terraform apply -input=false -auto-approve')

def teardown_resources():

    command_execution('terraform init',)
    command_execution('terraform destroy -auto-approve')

    # deleting the dynamo DB table
    print('Deleting dynamo db table...')
    dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
    dynamodb_client.delete_table(
        TableName='XXX-start-stop'
    )
    waiter = dynamodb_client.get_waiter('table_not_exists')
    waiter.wait(
        TableName='XXX-start-stop',
        WaiterConfig={
            'Delay': 5,
            'MaxAttempts': 10
        }
    )

if __name__ == '__main__':
    # teardown_resources()
    create_resources()

