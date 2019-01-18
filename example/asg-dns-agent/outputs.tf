output "asg_name" {
  value = "${aws_launch_configuration.test.id}"
}

output "vpc_internal_dns_id" {
  value = "${aws_route53_zone.test.id}"
}

output "vpc_internal_dns_name" {
  value = "${aws_route53_zone.test.name}"
}
