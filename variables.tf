variable "autoscale_handler_unique_identifier" {
  description = "asg_dns_handler"
}

variable "vpc_name" {
  description = "The name of the VPC"
}

variable "use_public_ip" {
  description = "Use public IP instead of private"
  default     = false
}

variable "update_instance_name_tag" {
  description = "Update the name tag of the instance"
  default     = true
}

variable "autoscale_route53zone_arn" {
  description = "The ARN of route53 zone associated with autoscaling group"
}

