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

variable "autoscale_route53zone_arn" {
  description = "The ARN of route53 zone associated with autoscaling group"
}

variable "hostname_tag_name" {
  description = "Name of tag with hostname pattern"
  default     = "asg:hostname_pattern"
  type        = string
}
