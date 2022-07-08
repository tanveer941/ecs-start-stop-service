### IAM Role ###
data "aws_iam_policy_document" "LambdaRoleAssumePolicy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      identifiers = ["lambda.amazonaws.com"]
      type = "Service"
    }
  }
}

## Lambda Role ##
resource "aws_iam_role" "LambdaECSStartStopRole" {
  name = "${var.ProjectName}-PipelineRole"
  assume_role_policy = data.aws_iam_policy_document.LambdaRoleAssumePolicy.json
  permissions_boundary = "arn:aws:iam::${data.aws_caller_identity.Me.account_id}:policy/ADSK-Boundary"
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "LambdaRoleECSAccess" {
  role = aws_iam_role.LambdaECSStartStopRole.id
  policy_arn = "arn:aws:iam::aws:policy/AmazonECS_FullAccess"
}

resource "aws_iam_role_policy_attachment" "LambdaExecutionRole" {
  role = aws_iam_role.LambdaECSStartStopRole.id
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}