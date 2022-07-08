variable "ProjectName" {
  type = string
  default = null
}
variable "GroupName" {}
variable "OwnerName" {}
variable "Moniker" {}
variable "AWSProfile" {
  type = string
  default = "default"
}
variable "ImageName" {
  type = string
  default = null
}
variable "ImageTag" {
  type = string
  default = null
}
variable "Vpc" {
  type = string
  default = null
}
variable "Subnet1" {
  type = string
  default = null
}
variable "UseContainer" {
  type = string
  default = "true"
}
variable "CodeBucket" {
  type = string
  default = null
}
variable "ContainerStateKey" {
  type = string
  default = null
}
variable "TFVersion" {
  type = string
  default = "1.1.5"
}
variable "CPArtifactBucket" {
  type = string
  default = null
}
variable "CodeZip" {
  type = string
  default = null
}
variable "ClusterName" {
  type = string
  default = null
}
variable "ServiceName" {
  type = string
  default = null
}
##### Local Variables #######
locals {
  common_tags = {
    group_name: var.GroupName
    owner_name: var.OwnerName
    "adsk:moniker": var.Moniker
  }
}