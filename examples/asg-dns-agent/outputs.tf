output "asg_name" {
  description = "The name of the autoscaling group"
  value       = aws_launch_configuration.test.id
}

output "vpc_internal_dns_id" {
  description = "ID of the internal dns hosted zone"
  value       = aws_route53_zone.test.id
}

output "vpc_internal_dns_name" {
  description = "The name of the dns hosted zone"
  value       = aws_route53_zone.test.name
}

