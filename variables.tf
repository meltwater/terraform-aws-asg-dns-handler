variable "autoscale_handler_unique_identifier" {
  description = "asg_dns_handler"
  type        = string
}

variable "vpc_name" {
  description = "The name of the VPC"
  type        = string
}

variable "use_public_ip" {
  description = "Use public IP instead of private"
  default     = false
  type        = bool
}

variable "autoscale_route53zone_arn" {
  description = "The ARN of route53 zone associated with autoscaling group"
  type        = string
}

variable "route53_record_ttl" {
  description = "TTL to use for the Route 53 Records created"
  default     = 300
  type        = number
}
