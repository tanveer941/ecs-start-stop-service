import boto3
import os


AWS_FILTERS = 'Filters'
AWS_FILTER_NAME = 'Name'
AWS_FILTER_VALUES = 'Values'
ARN = 'arn'
ARN_DELIMITER = ':'
ARN_SECONDARY_DELIMITER = '/'
ARN_LAST_INDEX = -1
AWS = 'aws'

ECS_CLUSTER = 'cluster'
ECS_SERVICE_ARN = 'serviceArn'
ECS_SERVICE_ARNS = 'serviceArns'
ECS_SERVICE = 'service'
ECS_SERVICES = 'services'
ECS_SERVICE_NAME = 'serviceName'
ECS_SERVICE_TASK_ARNS = 'taskArns'
ECS_SERVICE_TASK = 'task'
ECS_DESIRED_COUNT = 'desiredCount'


AAS_SERVICE_NAMESPACE = 'ServiceNamespace'
AAS_SCALABLE_DIMENSION = 'ScalableDimension'
AAS_SCALABLE_DIMENSION_ECS_DESIRED_COUNT = 'ecs:service:DesiredCount'
AAS_RESOURCE_ID = 'ResourceId'
AAS_RESOURCE_IDS = 'ResourceIds'
AAS_SCALABLE_TARGETS = 'ScalableTargets'
AAS_SUSPENDED_STATE = 'SuspendedState'
AAS_DYNAMIC_SCALING_IN = 'DynamicScalingInSuspended'
AAS_DYNAMIC_SCALING_OUT = 'DynamicScalingOutSuspended'
AAS_SCHEDULED_SCALING = 'ScheduledScalingSuspended'
AAS_MIN_CAPACITY = 'MinCapacity'


TYPE_ECS = 'ecs'
TYPE_APPLICATION_AUTO_SCALING = 'application-autoscaling'


ECS_ACTION = 'ecsAction'
ECS_ACTION_PAUSE = 'pause'
ECS_KILL_TASKS = 'ecsKillRunningTasks'


def handler(event, context):
    print("ECS start stop event: ", event)
    event_data = event
    # if event["resources"][0].endswith("-StopRule"):
    #     event_data[ECS_ACTION] = ECS_ACTION_PAUSE
    # else:
    #     event_data[ECS_ACTION] = 'revive'

    cluster_name = os.environ.get(ECS_CLUSTER)
    if cluster_name is None:
        cluster_name = event_data[ECS_CLUSTER]
    service_name = os.environ.get(ECS_SERVICE)
    if service_name is None:
        service_name = event_data[ECS_SERVICE]

    # event_data[ECS_CLUSTER] = os.environ.get(ECS_CLUSTER)
    # if event_data[ECS_CLUSTER] is None:
    #     raise_bad_input()
    # service_name = None
    # event_data[ECS_SERVICE] = os.environ.get(ECS_SERVICE)
    # if event_data[ECS_SERVICE] is None:
    #     service_name = event_data[ECS_SERVICE]


    if event_data[ECS_ACTION] == ECS_ACTION_PAUSE:
        kill_running_tasks = False
        event_data[ECS_KILL_TASKS] = os.environ.get(ECS_KILL_TASKS)
        if event_data[ECS_KILL_TASKS] is not None:
            kill_running_tasks = bool(event_data[ECS_KILL_TASKS])
        stop_service(cluster_name, service_name, kill_running_tasks)
    else:
        desired_count = 1
        event_data[ECS_DESIRED_COUNT] = os.environ.get(ECS_DESIRED_COUNT)
        if event_data[ECS_DESIRED_COUNT] is not None:
            desired_count = int(event_data[ECS_DESIRED_COUNT])
        start_service(cluster_name, service_name, desired_count)


def raise_bad_input():
    raise RuntimeError('Input must contain: ' + ECS_ACTION + ', ' + ECS_CLUSTER + ', and optionally ' + ECS_SERVICE + ', ' + ECS_DESIRED_COUNT + ', and ' + ECS_KILL_TASKS)


def stop_service(cluster_name, service_name, kill_running_tasks):
    # Get service detail
    print("pausing service", cluster_name, service_name, kill_running_tasks)
    ecs_client = boto3.client(TYPE_ECS)
    service_names = []
    if service_name is None:
        resp = ecs_client.list_services(**{
            ECS_CLUSTER: cluster_name
        })
        for service_arn in resp[ECS_SERVICE_ARNS]:
            service_names.append(get_arn_token(service_arn, ARN_SECONDARY_DELIMITER, ARN_LAST_INDEX))
    else:
        service_names.append(service_name)
    for service in service_names:
        resp = ecs_client.describe_services(**{
            ECS_CLUSTER: cluster_name,
            ECS_SERVICES: [
                service
            ]
        })
        service_detail = resp[ECS_SERVICES][0]
        service_arn = service_detail[ECS_SERVICE_ARN]
        service_resource_id = get_arn_token(service_arn, ARN_DELIMITER, ARN_LAST_INDEX)
        # Check if service has auto-scaler on desired count
        aas_client = boto3.client(TYPE_APPLICATION_AUTO_SCALING)
        resp = aas_client.describe_scalable_targets(**{
            AAS_SERVICE_NAMESPACE: TYPE_ECS,
            AAS_SCALABLE_DIMENSION: AAS_SCALABLE_DIMENSION_ECS_DESIRED_COUNT,
            AAS_RESOURCE_IDS: [
                service_resource_id
            ]
        })
        num_scalable_targets = len(resp[AAS_SCALABLE_TARGETS])
        if num_scalable_targets > 1:
            raise Exception("Too many scalable targets found: " + str(num_scalable_targets))
        if num_scalable_targets == 1:
            # Suspend auto scaling AND set minimum count to 0 to allow pausing the service
            aas_client.register_scalable_target(**{
                AAS_SERVICE_NAMESPACE: TYPE_ECS,
                AAS_SCALABLE_DIMENSION: AAS_SCALABLE_DIMENSION_ECS_DESIRED_COUNT,
                AAS_RESOURCE_ID: service_resource_id,
                AAS_MIN_CAPACITY: 0,
                AAS_SUSPENDED_STATE: {
                    AAS_DYNAMIC_SCALING_IN: True,
                    AAS_DYNAMIC_SCALING_OUT: True,
                    AAS_SCHEDULED_SCALING: True,
                }
            })
        # Pause ECS service by setting desired count to 0
        resp = ecs_client.update_service(**{
            ECS_CLUSTER: cluster_name,
            ECS_SERVICE: service,
            ECS_DESIRED_COUNT: 0
        })
        # Instantly kill any running tasks if requested
        if kill_running_tasks:
            resp = ecs_client.list_tasks(**{
                ECS_CLUSTER: cluster_name,
                ECS_SERVICE_NAME: service
            })
            for task in resp[ECS_SERVICE_TASK_ARNS]:
                ecs_client.stop_task(**{
                    ECS_CLUSTER: cluster_name,
                    ECS_SERVICE_TASK: task
                })
    print('Done')


def start_service(cluster_name, service_name, desired_count):
    print("reviving ", cluster_name, service_name, desired_count)
    # Get service detail
    ecs_client = boto3.client(TYPE_ECS)
    service_names = []
    if service_name is None:
        resp = ecs_client.list_services(**{
            ECS_CLUSTER: cluster_name
        })
        for service_arn in resp[ECS_SERVICE_ARNS]:
            service_names.append(get_arn_token(service_arn, ARN_SECONDARY_DELIMITER, ARN_LAST_INDEX))
    else:
        service_names.append(service_name)
    for service in service_names:
        resp = ecs_client.describe_services(**{
            ECS_CLUSTER: cluster_name,
            ECS_SERVICES: [
                service
            ]
        })
        service_detail = resp[ECS_SERVICES][0]
        service_arn = service_detail[ECS_SERVICE_ARN]
        service_resource_id = get_arn_token(service_arn, ARN_DELIMITER, ARN_LAST_INDEX)
        # Check if service has auto-scaler on desired count
        aas_client = boto3.client(TYPE_APPLICATION_AUTO_SCALING)
        resp = aas_client.describe_scalable_targets(**{
            AAS_SERVICE_NAMESPACE: TYPE_ECS,
            AAS_SCALABLE_DIMENSION: AAS_SCALABLE_DIMENSION_ECS_DESIRED_COUNT,
            AAS_RESOURCE_IDS: [
                service_resource_id
            ]
        })
        num_scalable_targets = len(resp[AAS_SCALABLE_TARGETS])
        if num_scalable_targets > 1:
            raise Exception("Too many scalable targets found: " + str(num_scalable_targets))
        if num_scalable_targets == 1:
            # Revive auto scaling
            aas_client.register_scalable_target(**{
                AAS_SERVICE_NAMESPACE: TYPE_ECS,
                AAS_SCALABLE_DIMENSION: AAS_SCALABLE_DIMENSION_ECS_DESIRED_COUNT,
                AAS_RESOURCE_ID: service_resource_id,
                AAS_SUSPENDED_STATE: {
                    AAS_DYNAMIC_SCALING_IN: False,
                    AAS_DYNAMIC_SCALING_OUT: False,
                    AAS_SCHEDULED_SCALING: False,
                }
            })
        # Revive ECS service by setting desired count to requested valid
        resp = ecs_client.update_service(**{
            ECS_CLUSTER: cluster_name,
            ECS_SERVICE: service,
            ECS_DESIRED_COUNT: desired_count
        })
    print('Done')


def get_arn_token(arn, delimiter, index):
    tokens = arn.split(delimiter)
    return tokens[index]

