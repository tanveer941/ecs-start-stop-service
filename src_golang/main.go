package main

import (
	"context"
	"fmt"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/applicationautoscaling"
	"github.com/aws/aws-sdk-go-v2/service/ecs"
	"log"
	"strings"
)

var serviceArn = ""

func pauseService(clusterName, serviceName string) {
	log.Printf("Pausing service....")
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		log.Fatal(err)
	}
	ecsClient := ecs.NewFromConfig(cfg)
	//output, err := ecs_client.ListServices(context.TODO(), &ecs.ListServicesInput{Cluster: aws.String(clusterName)})
	//serviceARNS := output.ServiceArns
	//fmt.Println(serviceARNS)
	output, err := ecsClient.DescribeServices(context.TODO(),
		&ecs.DescribeServicesInput{Cluster: aws.String(clusterName), Services: []string{serviceName}})
	//fmt.Println(output.Services)
	for _, object := range output.Services {
		serviceArn = aws.ToString(object.ServiceArn)
		log.Printf("Name of the service: %s", serviceArn)
		//log.Printf(aws.ToString(object.ServiceName))
	}
	serviceResourceId := strings.Split(serviceArn, ":")
	serviceResourceIdString := serviceResourceId[:len(serviceResourceId)-1]
	log.Printf("service Resource ID: %s", serviceResourceId)
	// ServiceNamespaceEcs "ecs:service:DesiredCount"
	autoscale_client := applicationautoscaling.NewFromConfig(cfg)
	scaleTargetOutput, err := autoscale_client.DescribeScalableTargets(context.TODO(),
		&applicationautoscaling.DescribeScalableTargetsInput{ServiceNamespace: "ecs",
			ScalableDimension: "ecs:service:DesiredCount",
			ResourceIds:       serviceResourceIdString})

	fmt.Println(len(scaleTargetOutput.ScalableTargets))
	// implement later
	//if len(scaleTargetOutput.ScalableTargets) == 1 {
	//	autoscale_client.RegisterScalableTarget(context.TODO(),
	//		&applicationautoscaling.RegisterScalableTargetInput{})
	//}
	//update service's desired count to 0
	ecsServiceOutput, err := ecsClient.UpdateService(context.TODO(),
		&ecs.UpdateServiceInput{Service: aws.String(serviceName),
			Cluster: aws.String(clusterName), DesiredCount: aws.Int32(0)})
	fmt.Println("ECS service update: %s ", ecsServiceOutput.ResultMetadata)
	// stop the running tasks
	listTasksOutput, err := ecsClient.ListTasks(context.TODO(),
		&ecs.ListTasksInput{Cluster: aws.String(clusterName),
			ServiceName: aws.String(serviceName)})
	for _, taskARN := range listTasksOutput.TaskArns {
		log.Printf("Killing tasks: %s", taskARN)
		ecsClient.StopTask(context.TODO(),
			&ecs.StopTaskInput{Cluster: aws.String(clusterName),
				Task: aws.String(taskARN)})
	}
}

func reviveService(clusterName, serviceName string) {
	log.Printf("Reviving service....")
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		log.Fatal(err)
	}
	ecsClient := ecs.NewFromConfig(cfg)
	ecsServiceOutput, err := ecsClient.UpdateService(context.TODO(),
		&ecs.UpdateServiceInput{Service: aws.String(serviceName),
			Cluster: aws.String(clusterName), DesiredCount: aws.Int32(1)})
	log.Printf("ecsServiceOutput: %s", ecsServiceOutput)
}

type MyEvent struct {
	Action  string `json:"ecsAction"`
	Cluster string `json:"cluster"`
	Service string `json:"service"`
}

func HandleRequest(pauseReviveEvent MyEvent) (string, error) {
	actionECS := pauseReviveEvent.Action
	clusterName := pauseReviveEvent.Cluster
	serviceName := pauseReviveEvent.Service
	fmt.Printf("Cluster-- %s for service-- %s , action is : %s \n", clusterName, serviceName, actionECS)
	if pauseReviveEvent.Action == "pause" {
		pauseService(clusterName, serviceName)
	} else {
		reviveService(clusterName, serviceName)
	}

	return fmt.Sprintf("Action taken-- %s , for Cluster-- %s and service-- %s",
		actionECS, clusterName, serviceName), nil
}

func main() {
	log.SetFlags(log.LstdFlags | log.Lmicroseconds)
	log.Printf("Start>>>>>>>>>>>>>>>>>>>>>>>>>>>")
	// To run locally comment the below line
	lambda.Start(HandleRequest)
	log.Printf("Stop>>>>>>>>>>>>>>>>>>>>>>>>>>>")
}
