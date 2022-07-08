FROM public.ecr.aws/lambda/python:3.9
WORKDIR /var/task
COPY ecs_start_stop.py ecs_start_stop.py
ENV ecsKillRunningTasks=true
ENV desiredCount=1
CMD ["ecs_start_stop.handler"]
