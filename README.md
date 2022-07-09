# ecs-start-stop-service
Pause and Revive ECS containers on the go. Helps cut costs when you do not need containers to run round the clock.

## How it works?
The code is packaged into a docker image and pushed to the Elastic Container Registry. A lambda function is used to run
the image by providing the correct inputs like the cluster and service name along with what action to be taken; to pause or revive a service.
Subsequently an Eventbridge rule is created to trigger the lambda based on a cron expression.

    Example: A website is hosted on an ECS container but if the website is not used over the weekend then it makes sense to pause/stop the container that is running by setting the cron expression on the event bridge.

## Presetup
Create `ecs_start_stop` ECR manually in the AWS console.  
The docker image linked to the lambda functions has to built and deployed manually. Following docker commands must be executed by going into the directory `./src`

`docker build -t ecs_start_stop:latest .`

`docker tag ecs_start_stop:latest [ACCOUNT_ID].dkr.ecr.[REGION].amazonaws.com/ecs_start_stop:[TAG_VERSION]`

`aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin [ACCOUNT_ID].dkr.ecr.[REGION].amazonaws.com`

`docker push [ACCOUNT_ID].dkr.ecr.[REGION].amazonaws.com/ecs_start_stop:[TAG_VERSION]`

### Variables update 
Update the tag version of the image URI in the lambda section of [main.tf](deployment/main.tf)

Update the necessary terraform variables in [terraform.tfvars.json](deployment/terraform.tfvars.json)

Update Dynamo DB table name in [provider.tf](deployment/provider.tf) and [deploy.py](deployment/deploy.py)

## Deployment
Now that the image is pushed to ECR and variable updated, the resources must be deployed to AWS.

To deploy resources run the function `create_resources()` in [deploy.py](deployment/deploy.py)
To delete resources run the function `teardown_resources()` in [deploy.py](deployment/deploy.py)