variable "instance_type" {
  description = "Size of the EC2 instance"
  default = "t2.medium"
}

variable "min_size" {
  description = "Minimum number of instances in the autoscaling group"
  default = "1"
}

variable "max_size" {
  description = "Maximum number of instances in the autoscaling group"
  default = "3"
}

variable "aws_region" {
  description = "Region for the VPC"
  default     = "eu-west-1"
}

variable "ami_id" {
  description = "AMIs by region"
  default     = "ami-f96c5280"
}

