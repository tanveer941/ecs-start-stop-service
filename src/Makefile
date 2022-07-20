ecr-login:
	aws ecr get-login-password --region $(REGION) | docker login --username AWS --password-stdin $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com

build:
	docker build -t ecs_start_stop:$(TAG_VERSION) .

prepare: build
	docker tag ecs_start_stop:$(TAG_VERSION) $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com/ecs_start_stop:$(TAG_VERSION)

ecr-deploy: prepare ecr-login
	docker push $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com/ecs_start_stop:$(TAG_VERSION)