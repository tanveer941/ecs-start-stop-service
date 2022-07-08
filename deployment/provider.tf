### Initialization Values ###
terraform {
  required_version = ">= 1.1.5"
  backend "s3" {
    bucket = "XXX-repo"
    key    = "XXX-start-stop/application.tfstate"
    region = "us-east-1"
    dynamodb_table = "XXX-start-stop"
    profile = "default"
  }
}

provider "aws" {
  version = "~> 3.0"
  region = "us-east-1"
  profile = var.AWSProfile
}