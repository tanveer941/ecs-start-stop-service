data "aws_caller_identity" "Me" {}
data "aws_region" "current" {}

### Lambda Resources ###
resource "aws_lambda_function" "ECSStartStopLambda" {
  function_name = "${var.ProjectName}-Lambda"
  role = aws_iam_role.LambdaECSStartStopRole.arn
  package_type = "Image"
  image_uri = "${data.aws_caller_identity.Me.account_id}.dkr.ecr.${data.aws_region.current.name}.amazonaws.com/ecs_start_stop:1"
  timeout = 300
  tags = local.common_tags
}

### CloudWatch Resources ###
resource "aws_cloudwatch_event_rule" "LambdaECSStopScheduler" {
  name = "${var.ProjectName}-StopRule"
  schedule_expression = "cron(30 14 ? * 2-6 *)"
  tags = local.common_tags
}
resource "aws_cloudwatch_event_target" "LambdaECSStopSchedulerTarget" {
  rule = aws_cloudwatch_event_rule.LambdaECSStopScheduler.name
  arn = aws_lambda_function.ECSStartStopLambda.arn
  input = jsonencode({
    "ecsAction": "pause",
    "cluster": "XXX-fargate-cluster",
    "service": "XXX-service"})
}

resource "aws_lambda_permission" "ECSStopLambdaPermission" {
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ECSStartStopLambda.arn
  principal = "events.amazonaws.com"
  source_arn = aws_cloudwatch_event_rule.LambdaECSStopScheduler.arn
}

resource "aws_cloudwatch_event_rule" "LambdaECSStartScheduler" {
  name = "${var.ProjectName}-StartRule"
  schedule_expression = "cron(30 3 ? * 2-6 *)"
  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "LambdaECSStartSchedulerTarget" {
  rule  = aws_cloudwatch_event_rule.LambdaECSStartScheduler.name
  arn   = aws_lambda_function.ECSStartStopLambda.arn
  input = jsonencode({
    "ecsAction": "revive",
    "cluster" : "XXX-fargate-cluster",
    "service" : "XXX-service"
  })
}

resource "aws_lambda_permission" "ECSStartLambdaPermission" {
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ECSStartStopLambda.arn
  principal = "events.amazonaws.com"
  source_arn = aws_cloudwatch_event_rule.LambdaECSStartScheduler.arn
}