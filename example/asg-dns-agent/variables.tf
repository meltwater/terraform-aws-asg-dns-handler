variable "instance_type" {
    default = "t2.medium"
}

variable "min_size" {
    default = "1"
}

variable "max_size" {
    default = "3"
}

variable "aws_region" {
  description = "Region for the VPC"
  default = "eu-west-1"
}

variable "ami_id" {
    description = "AMIs by region"
    default = "ami-f96c5280"
}
variable "availability_zones" {
  default = "eu-west-1a,eu-west-1b,eu-west-1c"
}
